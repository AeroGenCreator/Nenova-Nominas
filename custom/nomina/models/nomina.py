from odoo import api, fields, models


class NominaHistorial(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.nomina"
    _description = "Historico de Documento 'Nomina'."

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
    fecha_inicio = fields.Date(string="Fecha Inicio", required=True)
    fecha_fin = fields.Date(string="Fecha Fin", required=True)
    estado = fields.Selection(
        selection=[
            ("borrador", "Borrador"),
            ("calculando", "Calculando"),
            ("calculado", "Calculado"),
            ("validada", "Validada"),
            ("cancelada", "Cancelada"),
        ],
        string="Estado",
        default="borrador",
    )

    # PENDIENTE DE RELACIONAR
    # percepcion_ids
    # deducciones_ids

    active = fields.Boolean(string="Activo", default=True)
    total_percepciones = fields.Float(string="Total Percepciones", compute="")
    total_deducciones = fields.Float(string="Total Deducciones", compute="")
    neto = fields.Float(string="Neto", compute="")

    # === MODELO LÓGICA ===

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            borrador = vals.get("name", "Borrador")
            if borrador == "Borrador":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "nomina.nomina.sequence"
                    )
                    or "Borrador"
                )

    # === MODELO RESTRICCIONES ===
