from odoo import api, fields, models
from odoo.exceptions import ValidationError

MSG = (
    "Ya existe una referencia vacacional para este rango de años. "
    "Editar el registro existente o eliminar y crear uno nuevo."
)
LIM_MSG = (
    "Configuración de limites incorrecta o fuera de lógica. "
    "Ealua nuevamente tus rangos e intenta de nuevo."
)


class NominaVacacionalRangos(models.Model):
    # === MODELO CONFIG ===

    _name = "nomina.vacacional.rangos"
    _description = "Almacenar tabla referencia de vacaciones por ley."

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Rango",
        compute="computar_nombre_rango",
        store=True,
        readonly=True
    )
    limite_inferior = fields.Integer(
        string="Límite Inferior", aggregator="min", required=True, default=0,
    )
    limite_superior = fields.Integer(
        string="Límite Superior", aggregator="max", required=True, default=0,
    )
    dias_vacaciones = fields.Integer(
        string="Días Vacaciones", required=True, aggregator="sum", default=12,
    )
    categoria_id = fields.Many2one(
        string="Categoria",
        required=True,
        comodel_name="nomina.vacacional.categoria",
        ondelete="restrict",
    )
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LÓGICA ===

    @api.depends("limite_inferior", "limite_superior", "categoria_id")
    def computar_nombre_rango(self):
        """
        Computa el nombre del registro:
        Asi mismo computa el nombre cuando los limites son 0
        """
        for rec in self:
            NAME = False
            if rec.categoria_id:
                NAME = (
                    f"Años ({rec.limite_inferior} - {rec.limite_superior}) "
                    f"{rec.categoria_id.name}"
                )
            rec.name = NAME

    # === MODELO RESTRICCIONES ===

    _validar_rangos_ = models.Constraint(
        "UNIQUE(limite_inferior, limite_superior, categoria_id)", MSG
    )

    @api.constrains("limite_inferior", "limite_superior")
    def validar_rangos(self):
        for rec in self:
            if rec.limite_inferior and rec.limite_superior:
                validate = (
                    (rec.limite_inferior < 0),
                    (rec.limite_superior < 0),
                    (rec.limite_superior < rec.limite_inferior),
                )
                if any(validate):
                    raise ValidationError(LIM_MSG)
