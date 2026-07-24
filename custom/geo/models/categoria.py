from odoo import fields, models  # pyright: ignore


class GeoCategoria(models.Model):
    # === MODELO CONFIG ===
    _name = "geo.categoria"
    _description = "Cada registro: Categoria usada por modelos geolocalización."

    # === MODELO CAMPOS ===
    name = fields.Char(string="Categoria")
    ubicacion_empresa = fields.Boolean(string="Ubicación Empresa", default=False)
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LOGICA ===
    def _computar_hora_(self):
        for rec in self:
            rec.horas = fields.Datetime.now()

    # === MODELO RESTRICCIONES ===
    _unique_name_ = models.Constraint(
        "UNIQUE(name)", "Esta categoria ya existe en la base de datos."
    )
