from odoo import api, fields, models


class NominaRiesgoTrabajo(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.riesgo.trabajo"
    _description = "Registra los tipos de riesgo de trabajo y su factor."

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Factor de Riesgo", compute="computar_nombre", store=True
    )
    clase = fields.Char(string="Clase", required=True)
    factor = fields.Float(string="Factor", digits=(8, 7))
    descripcion = fields.Text(string="Descripción", required=True)
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LÓGICA ===

    @api.depends("factor")
    def computar_nombre(self):
        for rec in self:
            NAME = False
            if rec.factor:
                NAME = f"% {round(100 * rec.factor, 5)}"
            rec.name = NAME

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint(
        "UNIQUE(factor)", "Ya existe un registro con el mismo factor."
    )
