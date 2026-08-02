from odoo import api, fields, models


class NominaPrimaVacacionalFactor(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.prima.vacacional.factor"
    _description = "Cada registro - (Factor Prima Vacacional) %"

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Factor - Registro", compute="computar_nombre", store=True
    )
    factor = fields.Float(string="Factor", digits=(3, 2), default=0.25)
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LOGICA ===

    @api.depends("factor")
    def computar_nombre(self):
        for rec in self:
            NAME = False
            if rec.factor:
                NAME = f"{rec.factor * 100} %"
            rec.name = NAME

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint(
        "UNIQUE(NAME)", "Este factor de prima vacacional ya existe."
    )
