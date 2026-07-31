from odoo import fields, models


class NominaAguinaldoCategoria(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.aguinaldo.categoria"
    _description = "Brindar una etiqueta a los rangos de aguinaldos."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Categoría Nombre", required=True)
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO RESTRICCIONES ===

    models.Constraint(
        "UNIQUE(name)", "Esta categoría ya existe."
    )
