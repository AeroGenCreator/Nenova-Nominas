from odoo import fields, models  # pyright: ignore


class GeoEmployeeExt(models.Model):
    # === MODELO CONFIG
    _inherit = "hr.employee"

    # === MODELO NUEVOS CAMPOS ===
    plan_ids = fields.One2many(
        string="Lineas",
        comodel_name="geo.empleado.plan.linea",
        inverse_name="empleado_id",
    )

    # === MODELO LOGICA ===

    # === MODELO RESTRICCIONES ===
