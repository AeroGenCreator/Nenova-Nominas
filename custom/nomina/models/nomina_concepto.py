from odoo import fields, models

MSG = "Ya existe un concepto con el mismo código"

class NominaConcepto(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.concepto"
    _description = "Concepto de Nómina"

    # === MODELO CAMPOS ===

    name = fields.Char(string="Nombre", required=True)
    codigo = fields.Char(string="Código", required=True)
    tipo = fields.Selection(
        selection=[
            ("percepcion", "Percepción"),
            ("deduccion", "Deducción"),
        ],
        required=True,
    )
    grava_isr = fields.Boolean(string="Grava ISR", default=False)
    integra_imss = fields.Boolean(string="Integra IMSS", default=False)
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint("UNIQUE(codigo)", MSG)
