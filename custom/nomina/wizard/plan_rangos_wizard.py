from odoo import fields, models


class PlanRangosWizard(models.TransientModel):
    # === MODELO CONFIG ===

    _name = "nomina.plan.rangos.wizard"
    _description = (
        "Permite seleccionar una categoria de rango vacacional. "
        "Por este medio filtrar y relacionar al modelo padre que disparó "
        "el evento actual."
    )

    # === MODELO CAMPOS ===

    categoria_id = fields.Many2one(
        string="Categoría Vacacional",
        required=True,
        comodel_name="nomina.vacacional.categoria",
    )

    # === MODELO LÓGICA ===s

    def action_agregar_rangos(self):
        """
        Carga los rangos vacacionales segun la categoria seleccionada.
        Evita que se agreguen manualmente uno por uno.
        """

        # Operar un registro a la vez.
        self.ensure_one()
        # Obtencion del ID del registro padre que disparó el evento.
        ID = self.env.context.get("active_id", "")
        if not ID:
            return {"type": "ir.actions.act_window_close"}

        # Obtención de rango segun la categoria seleccionada.
        domain = [("categoria_id", "=", self.categoria_id.id)]
        recordests = self.env["nomina.vacacional.rangos"].search(domain)

        # Contrucción de la relacion:
        vals = []
        for rec in recordests:
            vals.append({
                "plan_id": ID,
                "rango_id": rec.id,
                "active": True,
            })

        self.env["nomina.plan.rango.rel"].create(vals)
