# Fichero Claude
import pytz

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

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_asistencia_fantasma()
        return records

    def write(self, vals):
        # Solo re-sincronizar si cambia algo que afecte la asistencia
        # fantasma: si deja/entra a 'falta_justificada', o si cambia la
        # fecha/empleado/estatus de una que ya lo es.
        CAMPOS_RELEVANTES = {"tipo", "fecha", "empleado_id", "active"}
        necesita_sync = bool(CAMPOS_RELEVANTES & set(vals))
        res = super().write(vals)
        if necesita_sync:
            self._sync_asistencia_fantasma()
        return res

    def _sync_asistencia_fantasma(self):
        """Mantiene sincronizado el 'hr.attendance' fantasma con el estado
        actual de la incidencia (ver Fase 5 del plan): se recrea si
        cambian tipo/fecha/empleado, se elimina si deja de ser
        'falta_justificada' o se archiva. La eliminación del registro de
        incidencia ya cascadea sola vía 'ondelete=cascade' en
        'hr.attendance.origen_incidencia_id' (FK a nivel de BD)."""
        Attendance = self.env["hr.attendance"]
        for rec in self:
            Attendance.search(
                [("origen_incidencia_id", "=", rec.id)]
            ).unlink()

            if rec.tipo != "falta_justificada" or not rec.active:
                continue

            jornada = rec.empleado_id.jornada_id
            if not jornada:
                continue

            linea = jornada.dia_ids.filtered(
                lambda l: l.dia_id.sequencia == rec.fecha.weekday()
            )[:1]
            if not linea or linea.estatus != "laboral":
                continue

            tz = pytz.timezone(rec.empleado_id.tz or "UTC")
            check_in_local = Attendance._hora_decimal_a_datetime_local(
                rec.fecha, linea.hora_inicio, tz
            )
            check_out_local = Attendance._hora_decimal_a_datetime_local(
                rec.fecha, linea.hora_termino, tz
            )
            Attendance.create({
                "employee_id": rec.empleado_id.id,
                "check_in": check_in_local.astimezone(pytz.utc).replace(
                    tzinfo=None
                ),
                "check_out": check_out_local.astimezone(pytz.utc).replace(
                    tzinfo=None
                ),
                "origen_incidencia_id": rec.id,
            })

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
