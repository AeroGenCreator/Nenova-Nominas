from odoo import fields, models


class WizardPlanVacacional(models.TransientModel):

    # === MODELO CONFIG ===

    _name = "wizard.plan.vacacional"
    _description = (
        "Permite seleccionar manualmente que empleado existe "
        "en el plan vacacional que disparó este evento."
    )

    # === MODELO CAMPOS ===

    empleado_ids = fields.Many2many(
        string="Empleados",
        comodel_name="hr.employee",
    )

    # === MODELO LÓGICA ===

    def action_relacionar_empleados(self):
        """
        Permite asignación de plan vacional de manera selectiva.
        Esto evita que se deba asignar desde el formulario "empleados".
        """

        # Operar sobre un solo registro
        self.ensure_one()

        # Obtener ID del registro padre que disparo el evento.
        ID = self.env.context.get("active_id", "")
        if not ID:
            return {"type": "ir.actions.act_window_close"}

        if not self.empleado_ids:
            return {"type": "ir.actions.act_window_close"}

        for rec in self.empleado_ids:
            rec.write({"plan_vacacional_id": ID})

    # === MODELO RESTRICCIONES ===
