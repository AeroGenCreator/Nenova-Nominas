from odoo import fields, models


class NominaVacacionCategoria(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.vacacion.categoria"
    _description = "Etiquetas Categoria para filtrar rangos vacacionales."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Categoria", required=True)
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LÓGICA ===

    # === MODELO RESTRICCIONES ===
