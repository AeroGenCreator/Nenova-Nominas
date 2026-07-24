from odoo import api, fields, models  # pyright: ignore


class GeoPlanUbicacionLinea(models.Model):
    # === MODELO CONFIG ===
    _name = "geo.plan.ubicacion.linea"
    _description = "Une en una linea (Plan - Ubicación)"

    # === MODELO CAMPOS ===
    name = fields.Char(string="Registro", compute="_computar_nombre_", store=True)
    plan_id = fields.Many2one(
        string="Plan", comodel_name="geo.plan", required=True, ondelete="cascade"
    )
    ubicacion_id = fields.Many2one(
        comodel_name="geo.ubicacion",
        string="Ubicación",
        ondelete="cascade",
        required=True,
    )
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LOGICA ===
    @api.depends("ubicacion_id", "plan_id")
    def _computar_nombre_(self):
        for rec in self:
            NAME = False
            validar = ((rec.ubicacion_id), (rec.plan_id))
            if all(validar):
                NAME = f"{rec.ubicacion_id.name} {rec.plan_id.name}"
            rec.name = NAME

    # === MODELO RESTRICCIONES ===
    _unica_combinacion_ = models.Constraint(
        "UNIQUE(ubicacion_id, plan_id)", "Esta localización ya existe en este plan."
    )
