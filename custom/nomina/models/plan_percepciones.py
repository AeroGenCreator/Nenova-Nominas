from odoo import fields, models


class NominaPlanPercepciones(models.Model):
    # === MODELO CONFIG ===

    _name = "nomina.plan.percepciones"
    _description = "Agrupa las percepciones y las relaciona a los empelados."

    # === MODELO CAMPOS ===
    name = fields.Char(string="Plan Nombre", required=True)
    active = fields.Boolean(string="Plan Activo", default=True)
    empleado_ids = fields.One2many(
        string="Empleados",
        comodel_name="hr.employee",
        inverse_name="plan_percepciones_id",
    )
    percepciones_ids = fields.Many2many(
        string="Percepciones", comodel_name="nomina.percepciones"
    )

    # === MODELO LOGICA ===

    # === MODELO RESTRICCIONES ===
