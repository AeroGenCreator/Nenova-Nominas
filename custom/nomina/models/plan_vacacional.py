from odoo import api, fields, models
from odoo.exceptions import ValidationError

MSG = (
    "Otro registro ya tiene este nombre. "
    "Editar el existente o en dado caso "
    "elimine el registro y vuelva a intentar."
)
CAD_MSG = (
    "Invalida combinación de caducidad. Se intenta asignar una caducidad "
    "no valida. No se pueden asignar valores negativos, los meses no pueden "
    "superar los '12' y los dias '31'."
)


class NominaPlanVacacional(models.Model):
    # === MODELO CONFIG ===

    _name = "nomina.plan.vacacional"
    _description = (
        "Cada Registro es: "
        "(Lineas de referencia vacacional con empleados asociados a este plan)."
    )

    # === MODELO CAMPOS ===

    name = fields.Char(string="Plan Vacacional", required=True)
    total_rangos = fields.Integer(
        string="Total Rangos", compute="computar_total_rangos"
    )
    total_empleados = fields.Integer(
        string="Total Empleados", compute="computar_total_empleados"
    )
    rango_ids = fields.One2many(
        string="Rangos Referencia Vacacional",
        comodel_name="nomina.plan.rango.rel",
        inverse_name="plan_id",
    )
    empleado_ids = fields.One2many(
        string="Empleados",
        comodel_name="hr.employee",
        inverse_name="plan_vacacional_id",
    )
    caduca_anhos = fields.Integer(
        string="Caducidad Años",
        default=0,
    )
    caduca_meses = fields.Integer(
        string="Caducidad Meses",
        default=0,
    )
    caduca_dias = fields.Integer(
        string="Caducidad Días",
        default=0,
    )
    minimo_anticipacion = fields.Integer(
        string="Mínimo Días Anticipación para Solicitar Vacaciones",
        default=1,
    )
    active = fields.Boolean(string="Plan Activo", default=True)

    # === MODELO LÓGICA ===

    @api.depends("rango_ids")
    def computar_total_rangos(self):
        for rec in self:
            TOTAL = 0
            if rec.rango_ids:
                TOTAL = len(rec.rango_ids)
            rec.total_rangos = TOTAL

    @api.depends("empleado_ids")
    def computar_total_empleados(self):
        for rec in self:
            TOTAL = 0
            if rec.empleado_ids:
                TOTAL = len(rec.empleado_ids)
            rec.total_empleados = TOTAL

    # === MODELO RESTRICCIONES ===

    _validar_registro_unico_ = models.Constraint("UNIQUE(name)", MSG)

    @api.constrains("caduca_anhos", "caduca_meses", "caduca_dias")
    def validar_caducidades(self):
        for rec in self:
            if rec.caduca_anhos < 0:
                raise ValidationError(CAD_MSG)
            elif rec.caduca_meses < 0 or rec.caduca_meses > 12:
                raise ValidationError(CAD_MSG)
            elif rec.caduca_dias < 0 or rec.caduca_dias > 31:
                raise ValidationError(CAD_MSG)
