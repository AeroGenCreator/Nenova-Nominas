from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

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
        string="Sueldo Bruto", compute="_compute_sueldo", store=True
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
        digits=(16, 4),
        compute="_compute_factor_integracion",
        store=True,
    )
    rango_seleccionado = fields.Integer(
        string="Rango Seleccionado",
        compute="_compute_rango_seleccionado",
        readonly=False,
        store=True,
        default=0,
    )
    percepcion_ids = fields.One2many(
        string="Percepción",
        comodel_name="percepcion.wizard",
        inverse_name="nomina_id",
    )

    # === MODELO LÓGICA ===

    @api.depends("empleado_id")
    def _compute_nombre(self):
        for rec in self:
            NAME = False
            if rec.empleado_id:
                NAME = f"{rec.empleado_id.name} - Nómina"
            rec.name = NAME

    @api.depends("empleado_id")
    def _compute_sueldo(self):
        for rec in self:
            SUELDO = False
            if rec.empleado_id:
                SUELDO = rec.empleado_id.sueldo_bruto
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

    @api.depends("empleado_id")
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

    # === MODELO ACCIONES ===

    def action_construir_nomina(self):
        for rec in self:
            pass
