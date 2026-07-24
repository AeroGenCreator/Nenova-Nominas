from odoo import fields, models  # pyright: ignore


class GeoUbicacion(models.Model):
    # === MODELO CONFIG ===
    _name = "geo.ubicacion"
    _description = (
        "Solo registra ubicaciones. "
        "Las ubicaciones pueden ser asignadas a planes de empleados."
    )

    # === MODELO CAMPOS ===
    name = fields.Char(string="Registro", compute="computar_nombre", readonly=True)
    categoria_id = fields.Many2one(
        string="Categoria", comodel_name="geo.categoria", ondelete="set null"
    )
    latitud = fields.Float(string="Latitud", digits=(10, 7), store=True)
    longitud = fields.Float(string="Longitud", digits=(10, 7), store=True)
    calle = fields.Char(string="Calle", store=True)
    area = fields.Char(string="Area", store=True)
    codigo_postal = fields.Char(string="Codigo Postal", store=True)
    direccion = fields.Char(string="Dirección", store=True)
    active = fields.Boolean(string="Activo", default=True)
    # Campo vacio para boton.
    gps_button = fields.Char()

    # === MODELO LOGICA ===
    def computar_nombre(self):
        for rec in self:
            NAME = False
            validate = ((rec.area), (rec.categoria_id))
            if all(validate):
                NAME = f"{rec.area} {rec.categoria_id.name}".strip()
            rec.name = NAME

    # === MODELO RESTRICCIONES ===
    _unico_registro_ = models.Constraint(
        "UNIQUE(latitud, longitud, categoria_id)",
        "La combincación de cooredenadas y categoria ya existe en la base de datos.",
    )
