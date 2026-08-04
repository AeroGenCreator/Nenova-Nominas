from odoo import api, fields, models


class NominaUMA(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.uma"
    _description = "Almacena el factor 'uma'."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Registro", compute="computar_nombre", store=True)
    uma = fields.Float(string="UMA", digits=(16, 2), required=True)
    fecha_activacion = fields.Date(
        string="Fecha Activación",
        default=lambda self: fields.Date.today()
    )
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO CONFIG ===

    @api.depends("uma")
    def computar_nombre(self):
        for rec in self:
            NAME = False
            if rec.uma:
                NAME = f"$ {rec.uma}"
            rec.name = NAME

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint("UNIQUE(uma)", "Este registro UMA ya existe.")
