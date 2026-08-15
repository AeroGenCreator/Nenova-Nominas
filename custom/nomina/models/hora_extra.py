# Fichero Claude
from odoo import api, fields, models
from odoo.exceptions import ValidationError

MSG_RANGO = "La hora de fin debe ser posterior a la hora de inicio."
MSG_FECHA = (
    "La fecha debe coincidir con la fecha de la hora de inicio. "
    "Capturas que cruzan la medianoche quedan fuera de alcance en esta versión."
)


class NominaHoraExtra(models.Model):
    """
    Captura manual y explícita de tiempo extra autorizado a pagar. Nunca se
    infiere de 'hr.attendance' (worked_hours - horas_programadas): separa
    "tiempo realmente trabajado" (reloj checador) de "tiempo extra
    autorizado a pagar" (decisión humana de RH/supervisor). Ver Modelo 4
    del plan.
    """

    # === MODELO CONFIG ===

    _name = "nomina.hora.extra"
    _description = "Registro manual de horas extra autorizadas a pagar"

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Hora Extra",
        compute="_compute_nombre",
        store=True,
    )
    empleado_id = fields.Many2one(
        string="Empleado", comodel_name="hr.employee", required=True
    )
    fecha = fields.Date(string="Fecha", required=True)
    hora_inicio = fields.Datetime(string="Hora Inicio", required=True)
    hora_fin = fields.Datetime(string="Hora Fin", required=True)
    horas = fields.Float(
        string="Horas",
        compute="_compute_horas",
        store=True,
        digits=(5, 2),
    )
    estado = fields.Selection(
        string="Estado",
        selection=[
            ("borrador", "Borrador"),
            ("autorizada", "Autorizada"),
        ],
        default="borrador",
        required=True,
    )
    attendance_id = fields.Many2one(
        string="Asistencia (referencia)",
        comodel_name="hr.attendance",
        help=(
            "Referencia informativa al registro de asistencia del mismo "
            "día. No se usa para derivar 'horas' — el tiempo extra es "
            "siempre la captura manual explícita."
        ),
    )
    justificacion = fields.Text(string="Justificación")

    # === MODELO LÓGICA ===

    @api.depends("empleado_id", "fecha", "horas")
    def _compute_nombre(self):
        for rec in self:
            NAME = False
            if rec.empleado_id and rec.fecha:
                NAME = (
                    f"{rec.empleado_id.name} - {rec.fecha} - {rec.horas:.2f}h"
                )
            rec.name = NAME

    @api.depends("hora_inicio", "hora_fin")
    def _compute_horas(self):
        for rec in self:
            HORAS = 0.0
            if (
                rec.hora_inicio
                and rec.hora_fin
                and rec.hora_fin > rec.hora_inicio
            ):
                HORAS = (
                    rec.hora_fin - rec.hora_inicio
                ).total_seconds() / 3600.0
            rec.horas = HORAS

    # === MODELO RESTRICCIONES ===

    @api.constrains("hora_inicio", "hora_fin")
    def _validar_rango_horas(self):
        for rec in self:
            if (
                rec.hora_inicio
                and rec.hora_fin
                and rec.hora_fin <= rec.hora_inicio
            ):
                raise ValidationError(MSG_RANGO)

    @api.constrains("fecha", "hora_inicio")
    def _validar_fecha_coincide(self):
        for rec in self:
            if rec.fecha and rec.hora_inicio:
                hora_inicio_local = fields.Datetime.context_timestamp(
                    rec, rec.hora_inicio
                )
                if rec.fecha != hora_inicio_local.date():
                    raise ValidationError(MSG_FECHA)
