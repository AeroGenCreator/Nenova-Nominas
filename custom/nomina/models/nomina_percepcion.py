from odoo import api, fields, models
from odoo.exceptions import ValidationError

MSG = (
    "El total calculado de importe no coincide con la "
    "suma de (gravantes y exentos)."
)


class NominaPercepcion(models.Model):
    # === MODELO CONFIG ===

    _name = "nomina.percepcion"
    _description = "Historico de Percepciones - Relacionado con Nominas"

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Percepción",
        compute="_compute_nombre",
        readonly=True,
        store=True
    )
    nomina_id = fields.Many2one(
        string="Nómina",
        comodel_name="nomina.nomina",
        ondelete="restrict",
        required=True,
        readonly=True,
    )
    concepto_id = fields.Many2one(
        string="Concepto",
        comodel_name="nomina.concepto",
        ondelete="restrict",
        required=True,
        readonly=True,
    )
    # Claude
    # Solo para condicionar el aviso de "validar con un contador" en la
    # vista (más simple/seguro que un 'invisible' con ruta punteada).
    concepto_codigo = fields.Char(
        string="Código de Concepto",
        related="concepto_id.codigo",
    )
    empleado_id = fields.Many2one(
        string="Empleado",
        comodel_name="hr.employee",
        related="nomina_id.empleado_id",
        store=True,
        readonly=True,
    )
    cantidad = fields.Float(
        string="Cantidad",
        default=1.0,
        digits=(16, 4),
        required=True,
        readonly=True,
        help="Cuantas unidades del concepto seran consideradas para el importe",
    )
    importe = fields.Float(
        string="Importe",
        default=0,
        digits=(16, 4),
        required=True,
        readonly=True,
        help="Valor unitario de esta percepcion",
    )
    importe_gravado = fields.Float(
        string="Importe Gravado",
        digits=(16, 4),
        default=0,
        required=True,
        readonly=True,
    )
    importe_exento = fields.Float(
        string="Importe Exento",
        digits=(16, 4),
        default=0,
        required=True,
        readonly=True,
    )
    total = fields.Float(
        string="Total",
        digits=(16, 4),
        compute="_compute_total",
        store=True,
        readonly=True,
    )
    active = fields.Boolean(string="Archivar", default=True)

    # === MODELO LÓGICA ===

    @api.depends("nomina_id.name", "concepto_id.name", "empleado_id.name")
    def _compute_nombre(self):
        for rec in self:
            NAME = False
            if rec.nomina_id and rec.concepto_id and rec.empleado_id:
                NAME = (
                    f"{rec.nomina_id.name} "
                    f"{rec.concepto_id.name} "
                    f"{rec.empleado_id.name}"
                )
            rec.name = NAME

    @api.depends("cantidad", "importe")
    def _compute_total(self):
        for rec in self:
            rec.total = fields.Float.round(
                rec.cantidad * rec.importe,
                precision_rounding=0.0001,
            )

    # Claude
    #
    # *** ADVERTENCIA: FORMULA FISCAL SIN VALIDAR POR UN CONTADOR ***
    # No usar el resultado de este método en una nómina real (producción)
    # sin que un contador confirme la interpretación de LFT art. 66-68 y
    # LISR art. 93 fracc. I aplicada aquí. Ver aviso visible en la vista
    # del concepto "Horas Extra" (nomina.concepto) y en la de percepción.
    #
    def _calcular_gravado_exento_horas_extra(
        self, horas_extra_ids, sueldo_diario, uma_diaria
    ):
        """(importe_total, importe_gravado, importe_exento) para un
        conjunto de 'nomina.hora.extra' autorizadas.

        Se agrupa por SEMANA CALENDARIO (ISO): la ley fija el límite de
        9 horas dobles y la exención de ISR por semana, no por el periodo
        completo de la nómina (que puede ser quincenal/mensual).

        Primeras 9 h/semana -> pagadas al doble.
        Excedente/semana    -> pagado al triple (grava 100%, sin exención).
        Exento              -> 50% de lo pagado al doble, tope 5 UMAs/semana.
        """
        LIMITE_HORAS_DOBLES_SEMANA = 9
        LIMITE_EXENCION_UMAS_SEMANA = 5

        tarifa_hora = (sueldo_diario / 8) if sueldo_diario else 0.0
        limite_exento_semana = uma_diaria * LIMITE_EXENCION_UMAS_SEMANA

        horas_por_semana = {}
        for he in horas_extra_ids:
            semana = he.fecha.isocalendar()[:2]
            horas_por_semana[semana] = (
                horas_por_semana.get(semana, 0.0) + he.horas
            )

        importe_total = 0.0
        importe_exento = 0.0
        for horas_semana in horas_por_semana.values():
            horas_dobles = min(horas_semana, LIMITE_HORAS_DOBLES_SEMANA)
            horas_triples = max(horas_semana - LIMITE_HORAS_DOBLES_SEMANA, 0.0)
            pago_doble = horas_dobles * tarifa_hora * 2
            pago_triple = horas_triples * tarifa_hora * 3
            importe_total += pago_doble + pago_triple
            importe_exento += min(pago_doble * 0.5, limite_exento_semana)

        importe_total = fields.Float.round(
            importe_total, precision_rounding=0.0001
        )
        importe_exento = fields.Float.round(
            importe_exento, precision_rounding=0.0001
        )
        importe_gravado = fields.Float.round(
            importe_total - importe_exento, precision_rounding=0.0001
        )
        return importe_total, importe_gravado, importe_exento

    # === MODELO RESTRICCIONES ===

    @api.constrains("total", "importe_gravado", "importe_exento")
    def _validar_total_(self):
        for rec in self:
            IMPORTES = rec.importe_gravado + rec.importe_exento
            if round(rec.total, 4) != round(IMPORTES, 4):
                raise ValidationError(MSG)
