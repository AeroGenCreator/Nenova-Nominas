from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError

VAL = "El rango de dias solicitado excede la cantidad permitida."
PAST_VACATION = (
    "Se esta seleccionando una fecha de inicio vacacional "
    "ubicada en el pasado. Solo puede pedir vacaciones en dias por venir."
)
CREATE_VAL = (
    "Faltan valores obligatorios. "
    "Dias apartados para vacaciones y el 'id' del derecho "
    "vacacional."
)

# Mensaje de error dinámico
def apartar_a_partir_de(dias: int, anticipacion: fields.Date):
    return (
        "Para solicitar un periodo de vacaciones segun su plan "
        f"vacacional, se requiere un lapso de {dias} dias mínimo. "
        f"En su caso a partir de {anticipacion}. "
        "Altere los rangos y vuelva a intentar."
    )


class NominaVacaciones(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.vacaciones"
    _description = "Cada registro es un rango vacacional usado por empleados."

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Registro", compute="computar_nombre_registro", store=True
    )
    empleado_id = fields.Many2one(
        string="Empleado",
        comodel_name="hr.employee",
        ondelete="restrict",
    )
    derecho_id = fields.Many2one(
        string="Derecho Vacacional",
        comodel_name="nomina.derecho.vacacional",
        ondelete="cascade",
        required=True,
    )
    comienza = fields.Date(string="Comienza", required=True)
    finaliza = fields.Date(string="Finaliza", required=True)
    disponibles = fields.Integer(
        string="Diás Disponibles para Derecho Vacacional Seleccionado",
        compute="computar_dias_disponles_en_derecho_seleccionado",
        store=False,
    )
    dias = fields.Integer(
        string="Total Días Vacaciones",
        compute="computar_dias_de_vacaciones",
        store=True,
    )
    anticipacion = fields.Date(
        string="Pedir vacaciones a partir del",
        compute="computar_minimo_anticipacion",
        store=False,
    )
    anho = fields.Integer(
        string="Año", compute="computar_anho_de_la_vacacion", store=True
    )
    active = fields.Boolean(string="Registro Activo", default=True)

    # === MODELO LÓGICA ===

    @api.depends("derecho_id", "dias")
    def computar_nombre_registro(self):
        for rec in self:
            NAME = False
            if rec.derecho_id and rec.dias:
                NAME = f"{rec.derecho_id.name} {rec.dias}"
            rec.name = NAME

    # OJO, EL DIA DE COMIENZO NO SE ESTA CONTANDO - ARREGLAR ESTA SITUACION !!!
    @api.depends("derecho_id", "comienza", "finaliza")
    def computar_dias_de_vacaciones(self):
        """
        Consideraciones

        Rango de fechas incluyentes:
        Se seleccionan
        EJ. (10 Enero) - (15 Enero)
        Dias de descanso 15 - 10 = 5

        Los descansos de jornada (No se cuentan como vacaciones)
        Sí en jornada; el descanso es el domingo - Y domingo cae (13 Enero)
        El día 13 no se cuenta como día vacacional.
        EJ. 15 - 10 = 5 -> 5 días vacaciones - 1 día descanso = 4 vacaciones

        Dias reales de vacaciones = 4
        """
        for rec in self:
            DIFERENCIA = False
            # Constante. Incluye el rango superior a la cuenta total.
            INCLUYENTE = 1
            if rec.comienza and rec.finaliza:
                # Se obtienen los codigos de weekday() 'datetime'
                jornada_dias = rec.empleado_id.jornada_id.dia_ids
                dias_codigo = [
                    dia.dia_id.sequencia
                    for dia in jornada_dias
                    if dia.estatus != "laboral"
                ]
                # Contador de días de descanso de la jornada.
                descansos = 0
                # Loop - Iterar el rango para encontrar días de descanso.
                FECHA_DE_CALCULO = rec.comienza
                while (
                    FECHA_DE_CALCULO <= rec.finaliza
                    or FECHA_DE_CALCULO >= rec.comienza
                ):
                    FECHA_DE_CALCULO += relativedelta(days=1)
                    # Si hay día de descanso. Descontamos de la cuenta final.
                    if FECHA_DE_CALCULO.weekday() in dias_codigo:
                        descansos += 1
                    if FECHA_DE_CALCULO > rec.finaliza:
                        break
                # (Finaliza - Comienza) - Descansos + Constante(Incluir 1)
                DIFERENCIA = (
                    (rec.finaliza - rec.comienza).days - descansos + INCLUYENTE
                )
            rec.dias = DIFERENCIA

    @api.depends("derecho_id")
    def computar_anho_de_la_vacacion(self):
        for rec in self:
            ANHO = False
            if rec.derecho_id:
                ANHO = rec.derecho_id.anho_activacion
            rec.anho = ANHO

    @api.depends("derecho_id")
    def computar_dias_disponles_en_derecho_seleccionado(self):
        for rec in self:
            NUMBER = False
            if rec.derecho_id:
                NUMBER = rec.derecho_id.dias_vacaciones
            rec.disponibles = NUMBER

    @api.depends("derecho_id")
    def computar_minimo_anticipacion(self):
        for rec in self:
            ANTICIPACION = False
            if rec.derecho_id:
                TODAY = fields.Date.today()
                MINIMO = rec.derecho_id.plan_id.minimo_anticipacion
                ANTICIPACION = TODAY + relativedelta(days=MINIMO)
            rec.anticipacion = ANTICIPACION

    # === LÓGICA AL CREAR REGISTRO ===

    @api.model_create_multi
    def create(self, dicc):
        """
        Descontar derechos vacacionales:
        Sí se crea un registro de vacaciones(Apartados).
        """
        record = super().create(dicc)

        derecho_id = record.derecho_id
        dias = record.dias

        validate = ((not derecho_id), (not dias))
        if any(validate):
            raise ValidationError(CREATE_VAL)

        disponibles = derecho_id.dias_vacaciones
        diferencia = disponibles - dias

        derecho_id.write({"dias_vacaciones": diferencia})

        return record

    # === LÓGICA AL BORRAR REGISTRO ===

    @api.ondelete(at_uninstall=False)
    def _unlink_recuperar_derechos_(self):
        """Repone los dias descontados de derecho vacacional"""
        for rec in self:
            validate = ((rec.dias), (rec.derecho_id), (rec.derecho_id.active))
            if all(validate):
                recuperar = rec.derecho_id.dias_vacaciones + rec.dias
                rec.derecho_id.write({"dias_vacaciones": recuperar})
            elif rec.dias:
                continue
            else:
                raise ValidationError("No se completo la petición")

    # === MODELO RESTRICCIONES ===

    @api.constrains("derecho_id", "comienza", "finaliza")
    def _validar_rango_permitido_(self):
        for rec in self:
            PERMITIDOS = rec.derecho_id.dias_vacaciones
            DIFERENCIA = (rec.finaliza - rec.comienza).days
            if DIFERENCIA > PERMITIDOS:
                raise ValidationError(VAL)

    @api.constrains("comienza")
    def _comienza_vacacion_despues_de_hoy_(self):
        for rec in self:
            TODAY = fields.Date.today()
            if rec.comienza < TODAY:
                raise ValidationError(PAST_VACATION)
            MINIMO = rec.derecho_id.plan_id.minimo_anticipacion
            ANTICIPACION = TODAY + relativedelta(days=MINIMO)
            if rec.comienza < ANTICIPACION:
                raise ValidationError(
                    apartar_a_partir_de(dias=MINIMO, anticipacion=ANTICIPACION)
                )
