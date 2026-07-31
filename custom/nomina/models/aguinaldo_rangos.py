from odoo import api, fields, models


class NominaAguinaldoRangos(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.aguinaldo.rangos"
    _description = (
        "Cada registro son rangos anuales que determinan la cantidad de dias "
        "por ser evaluados al determinar el aguinaldo del empleado."
    )

    # === MODELO CAMPOS ===

    name = fields.Char(string="Rango", compute="computar_nombre", store=True)
    categoria_id = fields.Many2one(
        string="Categoría", comodel_name="nomina.aguinaldo.categoria"
    )
    limite_inferior = fields.Integer(
        string="Límite Inferior", required=True, default=0
    )
    limite_superior = fields.Integer(
        string="Límite Superior", required=True, default=0
    )
    dias = fields.Integer(string="Días de Aguinaldo", required=True)
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LOGICA ===

    @api.depends("categoria_id", "limite_inferior", "limite_superior", "dias")
    def computar_nombre(self):
        for rec in self:
            NAME = False
            validate = (
                (rec.categoria_id),
                (rec.dias),
            )
            if all(validate):
                NAME = (
                    f"{rec.categoria_id.name} "
                    f"({rec.limite_inferior} - "
                    f"{rec.limite_superior}) "
                    f"{rec.dias}"
                )
            rec.name = NAME

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint(
        "UNIQUE(categoria_id, limite_inferior, limite_superior, dias)",
        "Este rango para aguinaldos ya existe."
    )
