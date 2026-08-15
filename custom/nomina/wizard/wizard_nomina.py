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
    fecha_inicio = fields.Date(string="Fecha Inicio", required=True)
    fecha_fin = fields.Date(string="Fecha Fin", required=True)
    empleado_id = fields.Many2one(
        string="Empleado",
        comodel_name="hr.employee",
        default=lambda self: self.env["hr.employee"].browse(
            self.env.context.get("active_id", "")
        ),
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
    total_dias = fields.Integer(
        string="Total Días",
        compute="_compute_total_dias",
        readonly=True,
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

    # === MODELO COMPUTADOS ===

    @api.depends("empleado_id")
    def _compute_nombre(self):
        for rec in self:
            NAME = False
            if rec.empleado_id:
                NAME = f"{rec.empleado_id.name} - Nómina"
            rec.name = NAME

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
    def _compute_total_dias(self):
        for rec in self:
            TOTAL = 0
            if rec.fecha_inicio and rec.fecha_fin:
                INCLUYENTE = rec.fecha_fin + timedelta(days=1)
                DIFF = INCLUYENTE - rec.fecha_inicio
                TOTAL = DIFF.days
            rec.total_dias = TOTAL

    # === MODELO RESTRICCIONES ===

    @api.constrains("fecha_inicio", "fecha_fin")
    def _validar_rango_fechas_(self):
        for rec in self:
            if rec.fecha_inicio and rec.fecha_fin:
                if rec.fecha_inicio > rec.fecha_fin:
                    raise ValidationError(DATE_ERROR)

    @api.constrains("modo_asistencia", "percepcion_ids")
    def _validar_datos_en_manual_(self):
        for rec in self:
            if rec.modo_asistencia == "manual" and not rec.percepcion_ids:
                raise ValidationError(
                    "El modo manual exige que los conceptos sean "
                    "especificados en la tabla de percepciones y deducciones."
                )

    # === MODELO ACCIONES ===

    def action_construir_nomina(self):
        self.ensure_one()

        # Inicializa (Montos para Horas Extras)
        gravado_he = 0.0
        exento_he = 0.0

        # Naturaleza de la operacion actual
        if self.modo_asistencia == "automatico":

            # (ASISTENCIAS) & (SUELDO)

            inicio = fields.Datetime.to_datetime(self.fecha_inicio)
            fin = fields.Datetime.to_datetime(self.fecha_fin) + timedelta(
                days=1
            )
            domain = [
                ("employee_id", "=", self.empleado_id.id),
                ("check_in", ">=", inicio),
                ("check_out", "<", fin)
            ]
            RECORDSETS = self.env["hr.attendance"].search(domain)
            concepto_sueldo = (
                self
                .env["nomina.concepto"]
                .search([("codigo", "=", "SUELDO")], limit=1)
            )
            if not concepto_sueldo:
                raise ValidationError(
                    "No existe el concepto 'SUELDO'. Asegurarse de agregar "
                    "dicho concepto de la siguiente manera codigo=SUELDO "
                    "en modelo 'nomina.concepto' para evitar este error."
                )
            DICC = {
                "nomina_id": self.id,
                "concepto_id": concepto_sueldo.id,
                "empleado_id": self.empleado_id.id,
                "cantidad": len(RECORDSETS),
                "importe": self.empleado_id.sueldo_diario,
            }
            singleton = self.percepcion_ids.filtered(
                lambda r: r.concepto_id.codigo == "SUELDO"
            )[:1]
            if not singleton:
                self.env["percepcion.wizard"].create(DICC)
            else:
                singleton.write(DICC)

            # (FALTAS)

            FALTAS = self.env["nomina.incidencia"].search([
                ("empleado_id", "=", self.empleado_id.id),
                ("fecha", ">=", self.fecha_inicio),
                ("fecha", "<=", self.fecha_fin),
                ("tipo", "=", "falta")
            ])
            concepto_falta = (
                self
                .env["nomina.concepto"]
                .search([("codigo", "=", "FALTA")], limit=1)
            )
            if not concepto_falta:
                raise ValidationError(
                    "No existe el concepto 'FALTA'. Asegurarse de agregar "
                    "dicho concepto de la siguiente manera codigo=FALTA "
                    "en modelo 'nomina.concepto' para evitar este error."
                )
            singleton = self.percepcion_ids.filtered(
                lambda r: r.concepto_id.codigo == "FALTA"
            )[:1]
            if FALTAS:
                ABSNTS = {
                    "nomina_id": self.id,
                    "concepto_id": concepto_falta.id,
                    "empleado_id": self.empleado_id.id,
                    "cantidad": len(FALTAS),
                    "importe": self.empleado_id.sueldo_diario,
                }
                if not singleton:
                    self.env["percepcion.wizard"].create(ABSNTS)
                else:
                    singleton.write(ABSNTS)
            else:
                if singleton:
                    singleton.unlink()

            # (HORAS EXTRAS) (UMA) (GRAVANTE) (EXENTO)

            HORAS_EXTRA = (
                self
                .env["nomina.hora.extra"]
                .search(
                    [
                        ("empleado_id", "=", self.empleado_id.id),
                        ("fecha", ">=", self.fecha_inicio),
                        ("fecha", "<=", self.fecha_fin),
                        ("estado", "=", "autorizada"),
                    ]
                )
            )
            uma_rec = self.env["nomina.uma"].search(
                [("fecha_activacion", "<=", self.fecha_fin)],
                order="fecha_activacion desc",
                limit=1,
            )
            if not uma_rec:
                raise UserError(
                    f"No se encontró UMA vigente al {self.fecha_fin}. "
                    "Registre el valor de la UMA en el catálogo."
                )
            concepto_he = (
                self
                .env["nomina.concepto"]
                .search([("codigo", "=", "HORAS_EXTRA")]
                )
            )
            if not concepto_he:
                raise ValidationError(
                    "No existe el concepto 'HORAS_EXTRA'. "
                    " Asegurarse de agregar dicho concepto de la "
                    "siguiente manera codigo=HORAS_EXTRA "
                    "en modelo 'nomina.concepto' para evitar este error."
                )
            singleton_he = self.percepcion_ids.filtered(
                lambda r: r.concepto_id.codigo == "HORAS_EXTRA"
            )[:1]
            if HORAS_EXTRA:
                total, gravado_he, exento_he = (
                    self._crear_percepcion_horas_extra_(
                        horas_extra=HORAS_EXTRA,
                        sueldo_diario=self.empleado_id.sueldo_diario,
                        uma_rec=uma_rec,
                    )
                )
                HE_TOTAL = sum(HORAS_EXTRA.mapped("horas"))
                DICC_HE = {
                    "nomina_id": self.id,
                    "concepto_id": concepto_he.id,
                    "empleado_id": self.empleado_id.id,
                    "cantidad": HE_TOTAL,
                    "importe": total / HE_TOTAL,
                }
                if not singleton_he:
                    self.env["percepcion.wizard"].create(DICC_HE)
                else:
                    singleton_he.write(DICC_HE)
            else:
                if singleton_he:
                    singleton_he.unlink()

        # Crea el registro nomina con folio
        nomina = self.env["nomina.nomina"].create(
            {
                "empleado_id": self.empleado_id.id,
                "fecha_inicio": self.fecha_inicio,
                "fecha_fin": self.fecha_fin,
            }
        )

        self._generar_deducciones_(nomina=nomina)

        # Se generan las percepciones de manera permanente
        # Se relacionan a la nomina recien creada.
        for linea in self.percepcion_ids:
            # Las faltas se generaron en el metodo de deducciones arriba.
            if linea.concepto_id.codigo == "FALTA":
                continue
            if linea.concepto_id.codigo != "HORAS_EXTRA":
                total = linea.total
                # grava_isr decide split gravado/exento
                if linea.concepto_id.grava_isr:
                    gravado = total
                    exento = 0.0
                else:
                    gravado = 0.0
                    exento = total
            else:
                gravado = gravado_he
                exento = exento_he

            self.env["nomina.percepcion"].create(
                {
                    "nomina_id": nomina.id,
                    "concepto_id": linea.concepto_id.id,
                    "cantidad": linea.cantidad,
                    "importe": linea.importe,
                    "importe_gravado": gravado,
                    "importe_exento": exento,
                }
            )

        # Calcula ISR e IMSS al cerrar wizard (despues de las lineas
        # automaticas: horas extra afecta la base gravada del ISR)
        nomina._calcular_isr()
        nomina._calcular_imss_obrero()
        nomina.write({"estado": "calculado"})

        # Abre la nomina generada al usuario
        return {
            "type": "ir.actions.act_window",
            "res_model": "nomina.nomina",
            "res_id": nomina.id,
            "view_mode": "form",
            "target": "current",
        }

    def _generar_deducciones_(self, nomina):
        """
        Las siguientes lineas son:
        1. Deducciones por 'retardo' e 'incidencia'.

        Este metodo se ejecuta antes de:
        1. Calculo de ISR
        2. Calculo de IMSS

        El dominio 'query' a los registros de 'asistencias'
        fueron computados justo en el momento cuando se creo la nomina actual.

        Revisar: 'nomina.nomina' campos computados y logica.
        """
        self.ensure_one()
        sueldo_diario = self.empleado_id.sueldo_diario

        # Retardos: una línea de deducción por evento, importe fijo.
        for attendance in nomina.attendance_ids.filtered("es_retardo"):
            self.env["nomina.deduccion"].create(
                {
                    "nomina_id": nomina.id,
                    "tipo": "retardo",
                    "concepto": f"Retardo {attendance.check_in}",
                    "importe": fields.Float.round(
                        sueldo_diario / 3, precision_rounding=0.0001
                    ),
                }
            )

        # (falta_justificada ya se paga sola vía asistencia fantasma).

        # Faltas no justificadas: UNA sola línea con el total de días.
        faltas = nomina.incidencia_ids.filtered(lambda r: r.tipo == "falta")
        dias_falta = sum(faltas.mapped("dias"))
        if dias_falta:
            self.env["nomina.deduccion"].create(
                {
                    "nomina_id": nomina.id,
                    "tipo": "falta",
                    "concepto": f"Falta ({dias_falta} día(s))",
                    "importe": sueldo_diario * dias_falta,
                }
            )

    def _crear_percepcion_horas_extra_(
        self,
        horas_extra,
        sueldo_diario,
        uma_rec,
    ):
        self.ensure_one()
        total, gravado, exento = (
            self
            .env["nomina.percepcion"]
            ._calcular_gravado_exento_horas_extra(
                    horas_extra, sueldo_diario, uma_rec.uma
                )
            )

        return total, gravado, exento
