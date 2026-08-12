from odoo import api, fields, models
from odoo.exceptions import UserError


class NominaHistorial(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.nomina"
    _description = "Historico de Documento 'Nomina'."

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Folio",
        required=True,
        readonly=True,
        default=lambda self: "Borrador",
    )
    empleado_id = fields.Many2one(
        string="Empleado", comodel_name="hr.employee", required=True
    )
    fecha_inicio = fields.Date(string="Fecha Inicio", required=True)
    fecha_fin = fields.Date(string="Fecha Fin", required=True)
    estado = fields.Selection(
        selection=[
            ("borrador", "Borrador"),
            ("calculando", "Calculando"),
            ("calculado", "Calculado"),
            ("validada", "Validada"),
            ("cancelada", "Cancelada"),
        ],
        string="Estado",
        default="borrador",
    )
    active = fields.Boolean(string="Activo", default=True)
    percepcion_ids = fields.One2many(
        string="Percepciones",
        comodel_name="nomina.percepcion",
        inverse_name="nomina_id",
    )
    deduccion_ids = fields.One2many(
        string="Deducciones",
        comodel_name="nomina.deduccion",
        inverse_name="nomina_id",
    )
    total_percepciones = fields.Float(
        string="Total Percepciones",
        compute="_compute_total_percepciones",
        store=True,
        digits=(16, 4),
    )
    total_deducciones = fields.Float(
        string="Total Deducciones",
        compute="_compute_total_deducciones",
        store=True,
        digits=(16, 4),
    )
    neto = fields.Float(
        string="Neto",
        compute="_compute_neto",
        store=True,
        digits=(16, 4),
    )

    # === MODELO LÓGICA ===

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            borrador = vals.get("name", "Borrador")
            if borrador == "Borrador":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "nomina.nomina.sequence"
                    )
                    or "Borrador"
                )
        return super().create(vals_list)

    # Claude
    @api.depends("percepcion_ids.total")
    def _compute_total_percepciones(self):
        for rec in self:
            rec.total_percepciones = sum(rec.percepcion_ids.mapped("total"))

    # Claude
    @api.depends("deduccion_ids.importe")
    def _compute_total_deducciones(self):
        for rec in self:
            rec.total_deducciones = sum(rec.deduccion_ids.mapped("importe"))

    # Claude
    @api.depends("total_percepciones", "total_deducciones")
    def _compute_neto(self):
        for rec in self:
            rec.neto = rec.total_percepciones - rec.total_deducciones

    # Claude
    def _calcular_isr(self):
        for rec in self:
            base_periodo = sum(rec.percepcion_ids.mapped("importe_gravado"))
            # Limpia ISR previo para recalcular
            rec.deduccion_ids.filtered(lambda d: d.tipo == "isr").unlink()
            if not base_periodo:
                # Todo exento: registra $0 para auditoría
                self.env["nomina.deduccion"].create({
                    "nomina_id": rec.id,
                    "tipo": "isr",
                    "concepto": "ISR",
                    "importe": 0.0,
                })
                continue

            dias_per = rec.empleado_id.periodo_pago_id.dias or 30.4
            # Proyecta al mes para aplicar tarifa
            base_mensual = base_periodo * (30.4 / dias_per)
            anho = rec.fecha_fin.year

            # Busca renglón por año y rango de base
            tabla = self.env["nomina.tabla.isr"].search([
                ("anho", "=", anho),
                ("limite_inferior", "<=", base_mensual),
                "|",
                ("limite_superior", ">=", base_mensual),
                ("limite_superior", "=", 0),
            ], order="limite_inferior desc", limit=1)

            if not tabla:
                raise UserError(
                    f"No se encontró tarifa ISR para el año {anho} "
                    f"con base mensual ${base_mensual:,.2f}. "
                    "Verifique que estén cargados los datos en Tarifa ISR."
                )

            isr_mensual = tabla.cuota_fija + (
                (base_mensual - tabla.limite_inferior) * tabla.tasa_excedente
            )

            # Busca subsidio del mismo año y rango
            subsidio_rec = self.env["nomina.tabla.subsidio"].search([
                ("anho", "=", anho),
                ("limite_inferior", "<=", base_mensual),
                "|",
                ("limite_superior", ">=", base_mensual),
                ("limite_superior", "=", 0),
            ], order="limite_inferior desc", limit=1)

            subsidio_mensual = subsidio_rec.subsidio if subsidio_rec else 0.0
            # ISR neto no puede ser negativo
            isr_neto_mensual = max(isr_mensual - subsidio_mensual, 0)
            # Convierte resultado al periodo real
            isr_periodo = round(isr_neto_mensual * (dias_per / 30.4), 4)

            self.env["nomina.deduccion"].create({
                "nomina_id": rec.id,
                "tipo": "isr",
                "concepto": "ISR",
                "importe": isr_periodo,
            })

    # Claude
    def action_calcular_isr(self):
        self._calcular_isr()

    # Claude
    def _calcular_imss_obrero(self):
        for rec in self:
            # UMA vigente a la fecha fin de la nomina
            uma_rec = self.env["nomina.uma"].search(
                [("fecha_activacion", "<=", rec.fecha_fin)],
                order="fecha_activacion desc",
                limit=1,
            )
            if not uma_rec:
                raise UserError(
                    f"No se encontró UMA vigente al {rec.fecha_fin}. "
                    "Registre el valor de la UMA en el catálogo."
                )

            uma_diaria = uma_rec.uma
            sdi_diario = rec.empleado_id.salario_integral

            # Tope LSS: SDI no puede exceder 25 UMAs
            tope_diario = uma_diaria * 25
            sdi_topado = min(sdi_diario, tope_diario)
            # LSS usa base de 30 dias para calcular mensual
            sdi_mensual = sdi_topado * 30

            # EM excedente 3 UMAs: 0.40% obrero
            limite_em_mensual = uma_diaria * 3 * 30
            excedente_em = max(sdi_mensual - limite_em_mensual, 0)
            cuota_em_excedente = excedente_em * 0.0040

            # EM prestaciones en dinero: 0.25% obrero
            cuota_em_dinero = sdi_mensual * 0.0025

            # Invalidez y Vida: 0.625% obrero
            cuota_iv = sdi_mensual * 0.00625

            # Cesantia en E.A. y Vejez: 1.125% obrero
            cuota_ceav = sdi_mensual * 0.01125

            imss_mensual = (
                cuota_em_excedente
                + cuota_em_dinero
                + cuota_iv
                + cuota_ceav
            )

            # Ajusta al periodo con dias_imss (base 30 LSS)
            dias_imss = rec.empleado_id.periodo_pago_id.dias_imss or 30
            imss_periodo = round(imss_mensual * (dias_imss / 30), 4)

            # Limpia IMSS previo para recalcular
            rec.deduccion_ids.filtered(
                lambda d: d.tipo == "imss_obrero"
            ).unlink()
            self.env["nomina.deduccion"].create({
                "nomina_id": rec.id,
                "tipo": "imss_obrero",
                "concepto": "Cuota Obrera IMSS",
                "importe": imss_periodo,
            })

    # Claude
    def action_calcular_imss(self):
        self._calcular_imss_obrero()

    # === MODELO RESTRICCIONES ===
