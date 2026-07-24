from odoo import fields, models


class NominaDias(models.Model):
    """
    Se declara este modelo de carga de días para poder
    renderizar cada opcion como una lista de checkbox en el wizard.
    'dias_wizard'.
    """
    # === MODELO CONFIG ===

    _name = "nomina.dias"
    _description = "Días de la semana como model independiente."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Día")
    codigo = fields.Char(string="Código")
    sequencia = fields.Integer(string="Sequencia")
