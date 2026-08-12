# Claude - Fichero Nuevo Hecho con IA
from odoo import fields, models


class NominaTablaISR(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.tabla.isr"
    _description = "Tarifa ISR mensual (Art. 96 LISR)"
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
    cuota_fija = fields.Float(
        string="Cuota Fija",
        digits=(16, 4),
        required=True,
    )
    tasa_excedente = fields.Float(
        string="Tasa sobre Excedente",
        digits=(8, 6),
        required=True,
        help="Porcentaje expresado como decimal (ej. 0.0640 = 6.40%)",
    )
    active = fields.Boolean(string="Activo", default=True)
