# Claude - Fichero Nuevo Hecho con IA
from odoo import api, fields, models


class NominaDeduccion(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.deduccion"
    _description = "Línea de Deducción en Nómina"

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Deducción",
        compute="_compute_nombre",
        store=True,
        readonly=True,
    )
    nomina_id = fields.Many2one(
        string="Nómina",
        comodel_name="nomina.nomina",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    # Claude
    tipo = fields.Selection(
        string="Tipo",
        selection=[
            ("isr", "ISR"),
            ("imss_obrero", "IMSS Obrero"),
            ("falta", "Falta"),
            ("retardo", "Retardo"),
            ("otra", "Otra"),
        ],
        required=True,
    )
    concepto = fields.Char(string="Concepto", required=True)
    importe = fields.Float(
        string="Importe",
        digits=(16, 4),
        required=True,
        default=0.0,
    )
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LÓGICA ===

    @api.depends("nomina_id.name", "tipo", "concepto")
    def _compute_nombre(self):
        for rec in self:
            NAME = False
            if rec.nomina_id and rec.tipo and rec.concepto:
                NAME = f"{rec.nomina_id.name} - {rec.concepto}"
            rec.name = NAME
