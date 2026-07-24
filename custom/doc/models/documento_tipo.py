from odoo import fields, models  # pyright: ignore


class DocumentoTipo(models.Model):
    # === Modelo Config ===
    _name = "documento.tipo"
    _description = "Modelo - Cada registro un tipo de documento"

    # === Modelo Campos ===
    name = fields.Char(string="Tipo de documento", required=True)
    active = fields.Boolean(string="Registro Activo", default=lambda self: True)
