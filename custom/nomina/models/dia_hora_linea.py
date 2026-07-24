from odoo import api, fields, models
from odoo.exceptions import ValidationError

UNICO_ERROR = (
    "La jornada actual ya cuenta con el día que se intenta inyectar. "
    "Se sugiere editar rangos de horas para el dia en cuestión. "
    "De lo contrario eliminar el registro duplicado e intetar de nuevo."
)
RANGO_INVALIDO = "Rango de horas invalido para la creación de registro."


class DiaHoraLinea(models.Model):
    """
    Dado que los dias son estaticos.
    Se usa este mdoelo como la linea (Dia - 'jornada diaria')
    """

    # === MODELO CONFIG ===
    _name = "nomina.dia.hora.linea"
    _description = (
        "Une en un solo registro Dia de la semana "
        "(Hora inicio - Hora fin) de jorndas."
    )

    # === MODELO CAMPOS ===
    name = fields.Char(
        string="Registro", compute="computar_nombre_dia", store=True
    )
    dia_id = fields.Many2one(
        string="Día", comodel_name="nomina.dias", required=True
    )
    hora_inicio = fields.Float(
        string="Hora inicio", digits=(5, 2), required=True, aggregator="min"
    )
    hora_termino = fields.Float(
        string="Hora termino", digits=(5, 2), required=True, aggregator="max"
    )
    estatus = fields.Selection(
        selection=[("laboral", "Laboral"),("descanso", "Descanso")],
        default="laboral"
    )
    active = fields.Boolean(string="Activo", default=True)
    jornada_id = fields.Many2one(
        string="Jornada",
        comodel_name="nomina.jornada",
        ondelete="cascade",
        required=True,
    )

    # === MODELO LÓGICA ===

    @api.depends("dia_id", "jornada_id")
    def computar_nombre_dia(self):
        for rec in self:
            NAME = False
            validate = ((rec.dia_id), (rec.jornada_id))
            if all(validate):
                NAME = f"{rec.dia_id.name} {rec.jornada_id.name}"
            rec.name = NAME

    # === MODELO RESTRICCIONES ===

    _registro_unico_ = models.Constraint(
        "UNIQUE(dia_id, jornada_id)", UNICO_ERROR
    )

    @api.constrains("hora_inicio", "hora_termino")
    def _validar_rangos_horas(self):
        MIN_LIM = 0
        MAX_LIM = 24
        for rec in self:
            is_data = ((rec.hora_inicio), (rec.hora_termino))
            if all(is_data):
                validate = (
                    (rec.hora_inicio < MIN_LIM),
                    (rec.hora_termino > MAX_LIM),
                    (rec.hora_inicio > rec.hora_termino),
                )
                if any(validate):
                    raise ValidationError(RANGO_INVALIDO)
