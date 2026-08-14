from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

DATE_ERROR = (
    "Invalido rango de fechas. "
    "La fecha de inicio no puede ser mayor a la fecha de fin."
)
RANGO_ERROR = (
    "El rango de fechas no coincide con la cantidad de días registrados "
    "sobre la percepción de sueldo. Asegurarse de que "
    "(fecha inicio - fecha fin) coincidan con la cantidad de días "
    "de la percepción sueldo. "
    "Esta advertencia solo existe para el concepto de 'sueldos'."
)


class NominaWizard(models.TransientModel):
    # === MODELO CONFIG ===

    _name = "nomina.wizard"
    _description = (
        "Almacena en buffer una nomina para el empleado "
        "desde el cual se haya disparado el evento."
    )

    # === MODELO CAMPOS ===

    name = fields.Char(string="Registro", compute="_compute_nombre", store=True)
    fecha_emision = fields.Date(
        string="Fecha de Emisión", default=lambda self: fields.Date.today()
    )
    fecha_inicio = fields.Date(string="Fecha Inicio", required=True)
    fecha_fin = fields.Date(string="Fecha Fin", required=True)
    empleado_id = fields.Many2one(
        string="Empleado",
        comodel_name="hr.employee",
        default=lambda self: self.env["hr.employee"].browse(
            self.env.context.get("active_id", "")
        ),
    )
    sueldo = fields.Float(
        string="Sueldo Bruto",
        compute="_compute_sueldo",
        store=True,
        digits=(16, 2),
    )
    periodicidad = fields.Char(
        string="Periodicidad", compute="_compute_periodo_pago", store=True
    )
    sueldo_diario = fields.Float(
        string="Sueldo Diario", compute="_compute_sueldo_diario", store=True
    )
    sdi = fields.Float(
        string="Salario Diario Integrado (SDI)",
        digits=(16, 4),
        compute="_compute_sdi",
        store=True,
    )
    factor_integracion = fields.Float(
        string="Factor Integración",
        digits=(16, 8),
        compute="_compute_factor_integracion",
        store=True,
    )
    rango_seleccionado = fields.Integer(
        string="Rango Seleccionado",
        compute="_compute_rango_seleccionado",
        readonly=False,
        store=True,
    )
    percepcion_ids = fields.One2many(
        string="Percepción",
        comodel_name="percepcion.wizard",
        inverse_name="nomina_id",
    )
    modo_asistencia = fields.Selection(
        string="Modo Asistencia",
        selection=[
            ("manual", "Manual"),
            ("automatico", "Automático"),
        ],
        default="manual",
        required=True,
        help=(
            "Automático: genera faltas, retardos y horas extra a partir "
            "de las asistencias e incidencias ya registradas del "
            "empleado en el rango. Manual: no se consulta nada — solo "
            "se procesan las percepciones capturadas a mano arriba."
        ),
    )

    # === MODELO LÓGICA ===

    @api.depends("empleado_id")
    def _compute_nombre(self):
        for rec in self:
            NAME = False
            if rec.empleado_id:
                NAME = f"{rec.empleado_id.name} - Nómina"
            rec.name = NAME

    @api.depends("empleado_id.sueldo_diario", "rango_seleccionado")
    def _compute_sueldo(self):
        for rec in self:
            SUELDO = 0
            if rec.empleado_id and rec.rango_seleccionado:
                SUELDO = fields.Float.round(
                    rec.empleado_id.sueldo_diario * rec.rango_seleccionado,
                    precision_rounding=0.01
                )
            rec.sueldo = SUELDO

    @api.depends("empleado_id")
    def _compute_periodo_pago(self):
        for rec in self:
            PERIODO = False
            if rec.empleado_id.periodo_pago_id:
                PERIODO = rec.empleado_id.periodo_pago_id.name
            rec.periodicidad = PERIODO

    @api.depends("empleado_id")
    def _compute_sueldo_diario(self):
        for rec in self:
            SUELDO_DIARIO = False
            if rec.empleado_id:
                SUELDO_DIARIO = rec.empleado_id.sueldo_diario
            rec.sueldo_diario = SUELDO_DIARIO

    @api.depends("empleado_id")
    def _compute_sdi(self):
        for rec in self:
            SDI = False
            if rec.empleado_id:
                SDI = rec.empleado_id.salario_integral
            rec.sdi = SDI

    @api.depends("empleado_id.factor_integracion")
    def _compute_factor_integracion(self):
        for rec in self:
            FACTOR = 0
            if rec.empleado_id:
                FACTOR = rec.empleado_id.factor_integracion
            rec.factor_integracion = FACTOR

    @api.depends("fecha_inicio", "fecha_fin")
    def _compute_rango_seleccionado(self):
        for rec in self:
            TOTAL = 0
            if rec.fecha_inicio and rec.fecha_fin:
                INCLUYENTE = rec.fecha_fin + timedelta(days=1)
                DIFF = INCLUYENTE - rec.fecha_inicio
                TOTAL = DIFF.days
            rec.rango_seleccionado = TOTAL

    # === MODELO RESTRICCIONES ===

    @api.constrains("fecha_inicio", "fecha_fin")
    def _validar_rango_fechas_(self):
        for rec in self:
            if rec.fecha_inicio and rec.fecha_fin:
                if rec.fecha_inicio > rec.fecha_fin:
                    raise ValidationError(DATE_ERROR)

    @api.constrains(
        "rango_seleccionado",
        "percepcion_ids.cantidad",
        "percepcion_ids.concepto_id.codigo",
    )
    def _validar_rango_dias_(self):
        """
        Valida que la cantidad de la percepcion sueldo coincida con el
        rango seleccionado en el wizard de nomina.
        """
        for rec in self:
            if rec.rango_seleccionado and rec.percepcion_ids:
                sueldo = rec.percepcion_ids.filtered(
                    lambda r: r.concepto_id.codigo == "SUELDO"
                )
                if sueldo:
                    if sueldo.cantidad != rec.rango_seleccionado:
                        raise ValidationError(RANGO_ERROR)

    @api.constrains("percepcion_ids")
    def _validar_percepciones_vacias_(self):
        for rec in self:
            if not rec.percepcion_ids:
                raise ValidationError(
                    "No se han agregados percepciones "
                    "Es necesario agregar como minimo el 'sueldo'."
                )

    # === MODELO ACCIONES ===

    # Claude
    def action_construir_nomina(self):
        for rec in self:
            # Crea el registro nomina con folio
            nomina = self.env["nomina.nomina"].create({
                "empleado_id": rec.empleado_id.id,
                "fecha_inicio": rec.fecha_inicio,
                "fecha_fin": rec.fecha_fin,
            })

            for linea in rec.percepcion_ids:
                total = linea.total
                # grava_isr decide split gravado/exento
                if linea.concepto_id.grava_isr:
                    gravado = total
                    exento = 0.0
                else:
                    gravado = 0.0
                    exento = total

                self.env["nomina.percepcion"].create({
                    "nomina_id": nomina.id,
                    "concepto_id": linea.concepto_id.id,
                    "cantidad": linea.cantidad,
                    "importe": linea.importe,
                    "importe_gravado": gravado,
                    "importe_exento": exento,
                })

            # Claude
            if rec.modo_asistencia == "automatico":
                rec._generar_lineas_automaticas(nomina)

            # Calcula ISR e IMSS al cerrar wizard (despues de las lineas
            # automaticas: horas extra afecta la base gravada del ISR)
            nomina._calcular_isr()
            nomina._calcular_imss_obrero()

            # Abre la nomina generada al usuario
            return {
                "type": "ir.actions.act_window",
                "res_model": "nomina.nomina",
                "res_id": nomina.id,
                "view_mode": "form",
                "target": "current",
            }

    # Claude
    def _generar_lineas_automaticas(self, nomina):
        """Modo automático (Fase 10): genera deducciones de falta/retardo
        y la percepción de horas extra a partir de hr.attendance /
        nomina.incidencia / nomina.hora.extra del rango, en vez de que RH
        las capture a mano. Reutiliza attendance_ids/incidencia_ids/
        hora_extra_ids (Fase 7) de la propia nómina recién creada, para
        no duplicar el dominio de búsqueda — lo que se ve en la pestaña
        "Días" es exactamente lo que alimentó este cálculo."""
        self.ensure_one()
        sueldo_diario = self.empleado_id.sueldo_diario

        # Retardos: una línea de deducción por evento, importe fijo.
        for attendance in nomina.attendance_ids.filtered("es_retardo"):
            self.env["nomina.deduccion"].create({
                "nomina_id": nomina.id,
                "tipo": "retardo",
                "concepto": f"Retardo {attendance.check_in}",
                "importe": sueldo_diario / 3,
            })

        # Faltas no justificadas: una sola línea con el total de días.
        # (falta_justificada ya se paga sola vía la asistencia fantasma
        # de la Fase 5 y no participa aquí).
        faltas = nomina.incidencia_ids.filtered(lambda i: i.tipo == "falta")
        dias_falta = sum(faltas.mapped("dias"))
        if dias_falta:
            self.env["nomina.deduccion"].create({
                "nomina_id": nomina.id,
                "tipo": "falta",
                "concepto": f"Falta ({dias_falta} día(s))",
                "importe": sueldo_diario * dias_falta,
            })

        # Horas extra autorizadas: una percepción con el reparto
        # gravado/exento de la Fase 9 (fórmula pendiente de validación
        # contable — ver aviso en la vista del concepto/percepción).
        horas_extra = nomina.hora_extra_ids
        if horas_extra:
            uma_rec = self.env["nomina.uma"].search(
                [("fecha_activacion", "<=", nomina.fecha_fin)],
                order="fecha_activacion desc",
                limit=1,
            )
            if not uma_rec:
                raise UserError(
                    f"No se encontró UMA vigente al {nomina.fecha_fin}. "
                    "Registre el valor de la UMA en el catálogo."
                )
            concepto_he = self.env["nomina.concepto"].search(
                [("codigo", "=", "HORAS_EXTRA")], limit=1
            )
            if not concepto_he:
                raise UserError(
                    "No existe el concepto 'HORAS_EXTRA' en el catálogo "
                    "de conceptos. Verifique data/nomina.concepto.csv."
                )
            total, gravado, exento = self.env[
                "nomina.percepcion"
            ]._calcular_gravado_exento_horas_extra(
                horas_extra, sueldo_diario, uma_rec.uma
            )
            if total:
                self.env["nomina.percepcion"].create({
                    "nomina_id": nomina.id,
                    "concepto_id": concepto_he.id,
                    "cantidad": 1,
                    "importe": total,
                    "importe_gravado": gravado,
                    "importe_exento": exento,
                })
