# Fichero Claude
from odoo import api, fields, models
from odoo.exceptions import ValidationError

MSG_DIAS = "El campo 'dias' solo admite 1.0 (día completo) o 0.5 (medio día)."
MSG_UNICO = (
    "Ya existe una incidencia registrada para este empleado en esta fecha. "
    "Edite el registro existente en vez de crear uno duplicado."
)


class NominaIncidencia(models.Model):
    """
    Registra ausencias del empleado (faltas, incapacidades, permisos).

    Se modela como un registro independiente y NO como una extensión de
    'hr.attendance', porque una falta es la AUSENCIA de un registro de
    asistencia: crear una asistencia "fantasma" para representar que el
    empleado no vino contaminaría los reportes y cálculos nativos de
    asistencia. La única excepción es 'falta_justificada', que sí genera
    una asistencia automática (ver Fase 5 del plan) porque ese día se paga
    igual que un día trabajado.
    """

    # === MODELO CONFIG ===

    _name = "nomina.incidencia"
    _description = "Incidencia de ausencia del empleado (falta, permiso, incapacidad)"

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Incidencia",
        compute="_compute_nombre",
        store=True,
    )
    empleado_id = fields.Many2one(
        string="Empleado", comodel_name="hr.employee", required=True
    )
    fecha = fields.Date(string="Fecha", required=True)
    tipo = fields.Selection(
        string="Tipo",
        required=True,
        selection=[
            ("falta", "Falta"),
            ("falta_justificada", "Falta Justificada"),
            ("incapacidad", "Incapacidad"),
            ("permiso_con_goce", "Permiso con Goce"),
            ("permiso_sin_goce", "Permiso sin Goce"),
        ],
    )
    dias = fields.Float(
        string="Días",
        default=1.0,
        digits=(4, 1),
        required=True,
        help="1.0 día completo o 0.5 medio día.",
    )
    justificacion = fields.Text(string="Justificación")
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LÓGICA ===

    @api.depends("empleado_id", "tipo", "fecha")
    def _compute_nombre(self):
        for rec in self:
            NAME = False
            if rec.empleado_id and rec.tipo and rec.fecha:
                dicc = dict(rec._fields["tipo"].selection)
                NAME = f"{rec.empleado_id.name} - {dicc.get(rec.tipo)} - {rec.fecha}"
            rec.name = NAME

    # === MODELO RESTRICCIONES ===

    # Evita que una misma fecha tenga dos incidencias distintas para el
    # mismo empleado (ej. "falta" y "permiso_con_goce" el mismo día), lo
    # cual sería ambiguo al momento de calcular la nómina.
    _unico_ = models.Constraint(
        "UNIQUE(empleado_id, fecha)", MSG_UNICO
    )

    @api.constrains("dias")
    def _validar_dias(self):
        for rec in self:
            if rec.dias not in (1.0, 0.5):
                raise ValidationError(MSG_DIAS)
