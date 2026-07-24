from odoo import api, fields, models


class NominaPlanRangoRel(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.plan.rango.rel"
    _description = "Relacion muchos a muchos (Une 'Plan V.' - 'Rango V.')."

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Relacion",
        compute="computar_relacion_nombre",
        store=True,
        readonly=True,
    )
    plan_id = fields.Many2one(
        string="Plan", comodel_name="nomina.plan.vacacional", ondelete="cascade"
    )
    rango_id = fields.Many2one(
        string="Rango Vacacional",
        comodel_name="nomina.vacacional.rangos",
        ondelete="restrict",
    )
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LÓGICA ===

    @api.depends("plan_id", "rango_id")
    def computar_relacion_nombre(self):
        for rec in self:
            NAME = False
            validate = ((rec.plan_id), (rec.rango_id))
            if all(validate):
                NAME = f"{rec.plan_id.name} {rec.rango_id.name}"
            rec.name = NAME

    # === MODELO RESTRICCIONES ===

    _validar_relacion_unica_ = models.Constraint(
        "UNIQUE(plan_id, rango_id)", "Esta relación de plan - rango ya existe."
    )
