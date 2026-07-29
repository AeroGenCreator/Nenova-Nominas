from odoo import fields, models


class PlanPercepcionesEmpleadoWizard(models.TransientModel):

    # === MODELO CONFIG ===

    _name = "plan.percepciones.empleado.wizard"
    _description = (
        "Permite seleccionar empleado y "
        "eventualmente agregarlos a un plan de percepciones"
    )

    # === MODELO CAMPOS ===

    empleado_ids = fields.Many2many(
        string="Empleados", comodel_name="hr.employee"
    )

    # === MODELO LOGICA ===

    def action_relacionar_empleados(self):
        # Asegurar que esta accion no se procese con varios recordsets.
        self.ensure_one()

        # Obtener ID del registro padre que disparo el evento.
        ID = self.env.context.get("active_id", "")
        if not ID:
            return {"type": "ir.actions.act_window_close"}

        if self.empleado_ids:
            for empleado in self.empleado_ids:
                empleado.write({"plan_percepciones_id": ID})
        else:
            return {"type": "ir.actions.act_window_close"}
