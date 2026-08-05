from odoo import fields, models

UNIQUE = "Esta percepcion ya existe. Se recomienda modificar la original."


class NominaPercepciones(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.percepciones"
    _description = (
        "Registra las percepciones como categorias (nombres). "
        "Se puede acceder a estos al generar una nómina(wizard)"
    )

    # === MODELO CAMPOS ===

    name = fields.Char(string="Percepción Nombre", required=True)
    active = fields.Boolean(string="Registro Activo", default=True)

    # === MODELO LÓGICA ===

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint("UNIQUE(name)", UNIQUE)
