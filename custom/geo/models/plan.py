from odoo import fields, models  # pyright: ignore


class GepPlan(models.Model):
    # === MODELO CONFIG ===
    _name = "geo.plan"
    _description = "Agrupa lineas de localizacion en un solo plan."

    # === MODELO CAMPOS ===
    name = fields.Char(string="Plan Nombre", required=True)
    plan_ubicacion_ids = fields.One2many(
        string="Localizaciones",
        comodel_name="geo.plan.ubicacion.linea",
        inverse_name="plan_id",
    )
    empleado_ids = fields.One2many(
        string="Empleados",
        comodel_name="geo.empleado.plan.linea",
        inverse_name="plan_id",
    )
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LOGICA ===

    # === MODELO RESTRICCIONES ===
    _unique_name_ = models.Constraint(
        "UNIQUE(name)",
        (
            f"Ya existe un plan para este empleado: {name.name}. "
            "Se recomienda buscar dicho registro y agregar las ubicaciones deseadas."
        ),
    )
