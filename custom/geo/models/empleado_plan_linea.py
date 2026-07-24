from odoo import api, fields, models  # pyright: ignore


class GeoEmpleadoPlanLinea(models.Model):
    # === MODELO CONFIG ===
    _name = "geo.empleado.plan.linea"
    _description = (
        "Une en un solo registro plan de ubicacioenes "
        "con empleados. Relacion Muchos a Muchos."
    )

    # === MODELO CAMPOS ===
    name = fields.Char(string="Registro", compute="computar_nombre")
    empleado_id = fields.Many2one(
        string="Empleado", comodel_name="hr.employee", ondelete="cascade"
    )
    plan_id = fields.Many2one(
        string="Plan", comodel_name="geo.plan", ondelete="cascade"
    )
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LOGICA ===
    @api.depends("empleado_id", "plan_id")
    def computar_nombre(self):
        for rec in self:
            NAME = False
            validar = ((rec.empleado_id), (rec.plan_id))
            if all(validar):
                NAME = f"{rec.empleado_id.name} {rec.plan_id.name}"
            rec.name = NAME

    # === MODELO RESTRICCIONES ===
    _registros_unicos_ = models.Constraint(
        "UNIQUE(empleado_id, plan_id)",
        "Erro de unicidad: Este registro relación (empleado - plan) ya existe.",
    )
