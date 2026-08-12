# Claude - Fichero Nuevo Hecho con IA
from odoo import fields, models


class NominaTablaSubsidio(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.tabla.subsidio"
    _description = "Tabla Subsidio al Empleo mensual"
    _order = "anho desc, limite_inferior asc"

    # === MODELO CAMPOS ===

    anho = fields.Integer(string="Año", required=True)
    limite_inferior = fields.Float(
        string="Límite Inferior",
        digits=(16, 4),
        required=True,
    )
    limite_superior = fields.Float(
        string="Límite Superior",
        digits=(16, 4),
        help="0 = sin límite superior (último renglón)",
    )
    subsidio = fields.Float(
        string="Subsidio Mensual",
        digits=(16, 4),
        required=True,
    )
    active = fields.Boolean(string="Activo", default=True)
