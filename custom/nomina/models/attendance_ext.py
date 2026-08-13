# Fichero Claude
from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models


class NominaAttendanceExt(models.Model):
    """
    Extiende 'hr.attendance' con lo que solo tiene sentido cuando el
    registro de asistencia YA EXISTE (horas programadas, retardo, tipo de
    día). Las faltas viven en 'nomina.incidencia' porque una falta es la
    AUSENCIA de un registro — no se crean asistencias "fantasma" para
    representarlas (ver Decisión de Arquitectura del plan), salvo el caso
    de 'falta_justificada' vía 'origen_incidencia_id' (Fase 5).
    """

    # === MODELO CONFIG ===

    _inherit = "hr.attendance"

    # === MODELO CAMPOS ===

    horas_programadas = fields.Float(
        string="Horas Programadas",
        compute="_compute_horas_programadas",
        digits=(5, 2),
        help="Horas programadas en la jornada del empleado para el día del check_in.",
    )
    retardo_minutos = fields.Integer(
        string="Minutos de Retardo",
        compute="_compute_retardo_minutos",
        help="Minutos tarde más allá de la tolerancia de la jornada. Solo informativo/auditoría.",
    )
    es_retardo = fields.Boolean(
        string="Es Retardo",
        compute="_compute_es_retardo",
        store=True,
        help="Dispara la deducción fija de retardo (sueldo_diario / 3) en el motor de nómina.",
    )
    tipo_dia = fields.Selection(
        string="Tipo de Día",
        selection=[
            ("laboral", "Laboral"),
            ("descanso_laborado", "Descanso Laborado"),
        ],
        compute="_compute_tipo_dia",
    )
    auto_checkout = fields.Boolean(
        string="Checkout Automático",
        default=False,
        help=(
            "El check_out fue generado por el cron de fin de jornada, no "
            "capturado por el empleado. Permite a RH identificarlo y "
            "corregirlo si el empleado justifica una salida distinta."
        ),
    )
    origen_incidencia_id = fields.Many2one(
        string="Incidencia de Origen",
        comodel_name="nomina.incidencia",
        ondelete="cascade",
        help=(
            "Seteado solo si esta asistencia es 'fantasma', creada "
            "automáticamente por una incidencia tipo 'falta_justificada'. "
            "Vacío en asistencias reales del reloj checador."
        ),
    )

    # === MODELO LÓGICA ===

    def _hora_local(self):
        """(weekday, hora_decimal) del check_in en la tz del empleado.

        check_in se guarda en UTC naive; sin esta conversión el retardo se
        calcularía contra la hora equivocada para empleados fuera de UTC.
        """
        self.ensure_one()
        tz = pytz.timezone(self.employee_id.tz or "UTC")
        check_in_local = pytz.utc.localize(self.check_in).astimezone(tz)
        hora_decimal = check_in_local.hour + check_in_local.minute / 60.0
        return check_in_local.weekday(), hora_decimal

    def _hora_decimal_a_datetime_local(self, fecha, hora_decimal, tz):
        """Convierte (fecha, hora en decimal, tz) a un datetime local
        tz-aware, normalizando el caso límite hora_decimal == 24 (fin de
        día) hacia las 00:00 del día siguiente. 'nomina.dia.hora.linea'
        valida hora_termino <= 24, así que este caso sí puede ocurrir."""
        dias_extra, hora_decimal = divmod(hora_decimal, 24)
        hora_h = int(hora_decimal)
        hora_m = round((hora_decimal - hora_h) * 60)
        if hora_m == 60:
            hora_m = 0
            hora_h += 1
        fecha_final = fecha + timedelta(days=int(dias_extra))
        return tz.localize(datetime.combine(fecha_final, time(hora_h, hora_m)))

    def _obtener_linea_dia(self):
        """Línea de 'nomina.dia.hora.linea' de la jornada del empleado que
        corresponde al día de la semana del check_in (0=Lunes..6=Domingo,
        igual que 'sequencia' en nomina.dias). Vacío si no hay jornada o no
        hay línea para ese día."""
        self.ensure_one()
        jornada = self.employee_id.jornada_id
        if not (self.check_in and jornada):
            return self.env["nomina.dia.hora.linea"]
        weekday, _ = self._hora_local()
        return jornada.dia_ids.filtered(
            lambda linea: linea.dia_id.sequencia == weekday
        )[:1]

    @api.depends(
        "check_in",
        "employee_id.tz",
        "employee_id.jornada_id.dia_ids.dia_id",
        "employee_id.jornada_id.dia_ids.hora_inicio",
        "employee_id.jornada_id.dia_ids.hora_termino",
    )
    def _compute_horas_programadas(self):
        for rec in self:
            HORAS = 0.0
            linea = rec._obtener_linea_dia()
            if linea:
                HORAS = linea.hora_termino - linea.hora_inicio
            rec.horas_programadas = HORAS

    @api.depends(
        "check_in",
        "employee_id.tz",
        "employee_id.jornada_id.tolerancia_entrada",
        "employee_id.jornada_id.dia_ids.dia_id",
        "employee_id.jornada_id.dia_ids.hora_inicio",
        "employee_id.jornada_id.dia_ids.estatus",
        "origen_incidencia_id",
    )
    def _compute_retardo_minutos(self):
        for rec in self:
            MINUTOS = 0
            # Una asistencia fantasma (falta_justificada) nunca es retardo.
            if not rec.origen_incidencia_id:
                linea = rec._obtener_linea_dia()
                if linea and linea.estatus == "laboral":
                    _, hora_local = rec._hora_local()
                    jornada = rec.employee_id.jornada_id
                    entrada_permitida = (
                        linea.hora_inicio + jornada.tolerancia_entrada / 60.0
                    )
                    diferencia = hora_local - entrada_permitida
                    if diferencia > 0:
                        MINUTOS = round(diferencia * 60)
            rec.retardo_minutos = MINUTOS

    # Compute separado de '_compute_retardo_minutos': Odoo desaconseja mezclar
    # campos store=True y store=False en un mismo método compute (genera un
    # UserWarning de 'compute_sudo'/'store' inconsistentes al cargar el módulo).
    @api.depends("retardo_minutos")
    def _compute_es_retardo(self):
        for rec in self:
            rec.es_retardo = rec.retardo_minutos > 0

    @api.depends(
        "check_in",
        "employee_id.tz",
        "employee_id.jornada_id.dia_ids.dia_id",
        "employee_id.jornada_id.dia_ids.estatus",
    )
    def _compute_tipo_dia(self):
        for rec in self:
            TIPO = False
            linea = rec._obtener_linea_dia()
            if linea:
                TIPO = (
                    "laboral" if linea.estatus == "laboral"
                    else "descanso_laborado"
                )
            rec.tipo_dia = TIPO

    # === CRON ===

    def _cron_auto_checkout(self):
        """Cierra automáticamente las asistencias sin check_out cuya
        jornada ya terminó. Alcance v1: solo turnos diurnos
        (hora_inicio < hora_termino) — turnos nocturnos quedan pendientes
        para una fase posterior (ver plan)."""
        abiertas = self.env["hr.attendance"].search([("check_out", "=", False)])
        ahora_utc = pytz.utc.localize(fields.Datetime.now())
        for att in abiertas:
            jornada = att.employee_id.jornada_id
            if not jornada:
                continue
            linea = att._obtener_linea_dia()
            if not linea or linea.hora_inicio > linea.hora_termino:
                continue
            tz = pytz.timezone(att.employee_id.tz or "UTC")
            check_in_local = pytz.utc.localize(att.check_in).astimezone(tz)
            checkout_local = att._hora_decimal_a_datetime_local(
                check_in_local.date(), linea.hora_termino, tz
            )
            if ahora_utc > checkout_local:
                att.write({
                    "check_out": checkout_local.astimezone(pytz.utc).replace(
                        tzinfo=None
                    ),
                    "auto_checkout": True,
                })
