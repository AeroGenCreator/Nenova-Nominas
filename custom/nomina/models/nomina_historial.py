from odoo import api, fields, models


class NominaHistorial(models.Model):
    # === MODELO CONFIG ===

    _name = "nomina.historial"
    _description = "Almacena cada nómina validada."

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Folio",
        required=True,
        readonly=True,
        default=lambda self: "Borrador",
    )
    empleado_id = fields.Many2one(
        string="Empleado", comodel_name="hr.employee", required=True
    )
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LÓGICO ===

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            borrador = vals.get("name", "Borrador")
            if borrador == "Borrador":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "nomina.historial.sequence"
                    )
                    or "Borrador"
                )

    # === MODELO RESTRICCIONES ===
