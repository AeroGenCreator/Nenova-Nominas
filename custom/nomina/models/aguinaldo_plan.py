from odoo import fields, models


class NominaAguinaldoPlan(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.aguinaldo.plan"
    _description = "Agrupa empleados y rangos de aguinaldos."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Plan Nombre", required=True)
    empleado_ids = fields.Many2many(
        string="Empleados", comodel_name="hr.employee"
    )
    rango_ids = fields.Many2many(
        string="Aguinaldo Rangos", comodel_name="nomina.aguinaldo.rangos"
    )
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LOGICA ===

    def action_agregar_todos_empleados(self):
        self.ensure_one()
        self.env["hr.employee"].search([]).aguinaldo_plan_id = self.id

    # === MODELO RESTRICCIONES ===

    _unico_ = models.Constraint(
        "UNIQUE(name)", "Este plan de aguinaldos ya existe."
    )
