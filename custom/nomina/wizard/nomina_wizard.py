from datetime import date

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class NominaWizard(models.TransientModel):
    # === MODELO CONFIG ===

    _name = "nomina.wizard"
    _description = (
        "Almacena en buffer una nomina para el empleado "
        "desde el cual se haya disparado el evento."
    )

    # === MODELO CAMPOS ===

    name = fields.Char(string="Registro", compute="computar_nombre", store=True)
    empleado_id = fields.Many2one(
        string="Empleado",
        comodel_name="hr.employee",
        default=lambda self: self.env["hr.employee"].browse(
            self.env.context.get("active_id", "")
        ),
    )
    sueldo = fields.Float(string="Sueldo Bruto", compute="computar_sueldo")
    periodicidad = fields.Char(
        string="Periodicidad", compute="computar_periodicidad"
    )
    sueldo_diario = fields.Float(
        string="Sueldo Diario", compute="computar_sueldo_diario"
    )
    sdi = fields.Float(
        string="Salario Diario Integrado (SDI)",
        digits=(16, 4),
        compute="computar_salario_diario_integrado",
    )
    uma_id = fields.Many2one(
        string="UMA",
        comodel_name="nomina.uma",
        default=lambda self: self.computar_uma_mas_reciente(),
    )
    factor_riesgo_trabajo_id = fields.Many2one(
        string="Factor Riesgo de Trabajo",
        comodel_name="nomina.riesgo.trabajo",
        default=lambda self: self.computar_factor_riesgo_minimo(),
    )
    total_dias = fields.Integer(
        string="Total Días",
        compute=lambda self: self.computar_total_dias(),
        readonly=False,
    )
    percepciones_total = fields.Float(
        string="Perpeciones Suma Monto Total (Diarios)",
        digits=(16, 4),
        compute="computar_monto_total_percepciones",
    )
    salario_base_cotizacion = fields.Float(
        string="Salario Base de Cotización (SBC)",
        digits=(16, 4),
        compute="computar_salario_base_cotizacion",
        help="Monto (Determina cuotas 'Obrero-Patronal')",
    )
    percepciones_ids = fields.One2many(
        string="Perpeciones",
        comodel_name="percepcion.wizard",
        inverse_name="nomina_id",
    )
    fecha_emision = fields.Date(
        string="Fecha de Emisión", default=lambda self: fields.Date.today()
    )

    # === MODELO LÓGICA ===

    @api.depends("empleado_id")
    def computar_nombre(self):
        for rec in self:
            NAME = False
            if rec.empleado_id:
                NAME = f"{rec.empleado_id.name} - Nómina"
            rec.name = NAME

    @api.depends("empleado_id")
    def computar_sueldo(self):
        for rec in self:
            SUELDO = False
            if rec.empleado_id:
                SUELDO = rec.empleado_id.sueldo_bruto
            rec.sueldo = SUELDO

    @api.depends("empleado_id")
    def computar_periodicidad(self):
        for rec in self:
            PERIODO = False
            if rec.empleado_id.periodo_pago_id:
                PERIODO = rec.empleado_id.periodo_pago_id.name
            rec.periodicidad = PERIODO

    @api.depends("empleado_id")
    def computar_sueldo_diario(self):
        for rec in self:
            SUELDO_DIARIO = False
            if rec.empleado_id:
                SUELDO_DIARIO = rec.empleado_id.sueldo_diario
            rec.sueldo_diario = SUELDO_DIARIO

    @api.depends("empleado_id")
    def computar_salario_diario_integrado(self):
        for rec in self:
            SDI = False
            if rec.empleado_id:
                SDI = rec.empleado_id.salario_integral
            rec.sdi = SDI

    def computar_uma_mas_reciente(self):
        UMA = False
        try:
            umas = self.env["nomina.uma"].search([])
            newest_uma = sorted(
                umas, key=lambda r: r.fecha_activacion, reverse=True
            )
            if newest_uma:
                UMA = newest_uma[0]
        except Exception:
            pass
        return UMA

    def computar_factor_riesgo_minimo(self):
        RIESGO = False
        try:
            riesgos = self.env["nomina.riesgo.trabajo"].search([])
            minimo = sorted(riesgos, key=lambda r: r.factor, reverse=False)
            if minimo:
                RIESGO = minimo[0]
        except Exception:
            pass
        return RIESGO

    @api.depends("percepciones_ids")
    def computar_monto_total_percepciones(self):
        for rec in self:
            TOTAL = 0
            if rec.percepciones_ids:
                cantidades_diarias = [
                    r.monto_diario
                    for r in rec.percepciones_ids if r.integra_sbc
                ]
                TOTAL = sum(cantidades_diarias)
            rec.percepciones_total = TOTAL

    @api.depends("sdi","percepciones_total")
    def computar_salario_base_cotizacion(self):
        for rec in self:
            SBC = 0
            if rec.sdi:
                SBC = rec.sdi + rec.percepciones_total
            rec.salario_base_cotizacion = SBC

    @api.depends("empleado_id", "periodicidad")
    def computar_total_dias(self):
        """Automático: Busca asistencias o regresa 0."""
        for rec in self:
            # Por defecto se asignan 0 dias.
            DIAS = 0

            # Si no esta asignado 'empleado' o 'periodicidad', asigna 0.
            if not rec.periodicidad or not rec.empleado_id:
                rec.total_dias = DIAS
                return

            # Se busca 'singleton' periodo. De lo contrario asigna 0.
            p_domain = [("name", "=", rec.periodicidad)]
            periodo = rec.env["nomina.periodo.pago"].search(p_domain)
            if not periodo:
                rec.total_dias = DIAS
                return

            # Se determina dia actual(Referencia)
            TODAY = fields.Date.today()
            THIS_MONTH = TODAY.month
            THIS_YEAR = TODAY.year
            THIS_DAY = TODAY.day

            # Caso cuando periodo ANUAL
            if periodo.dias_imss == 365:
                # Se restan 12 meses a fecha actual (ANHO)
                RANGE_START = date(THIS_YEAR, THIS_MONTH, 1) - relativedelta(
                    months=12
                )
                # Mes actual 12, y excluyente el mes proximo "13".
                RANGE_ENDNG = date(THIS_YEAR, THIS_MONTH, 1) + relativedelta(
                    months=1
                )

            # Caso cuando periodo mayor a MES & modulo de 30 con residuo 0.
            elif periodo.dias_imss > 30 and periodo.dias_imss % 2 == 0:
                MESES = (periodo.dias_imss // 30) - 1
                RANGE_START = date(THIS_YEAR, THIS_MONTH, 1) - relativedelta(
                    months=MESES
                )
                RANGE_ENDNG = date(THIS_YEAR, THIS_MONTH, 1) + relativedelta(
                    months=1
                )
            # Caso cuando periodo igual a MENSUAL.
            elif periodo.dias_imss == 30:
                RANGE_START = date(THIS_YEAR, THIS_MONTH, 1)
                RANGE_ENDNG = date(THIS_YEAR, THIS_MONTH, 1) + relativedelta(
                    months=1
                )
            # Caso cuando periodo < 30 || periodo > 30 & modulo residuo != 0.
            else:
                # Caso cuando QUINCENAS.
                if periodo.dias_imss in (15, 14):
                    MESES = 0
                    LIM_INFERIOR = 1
                    LIM_SUPERIOR = periodo.dias_imss + 1
                    if THIS_DAY > periodo.dias_imss:
                        LIM_INFERIOR = periodo.dias_imss + 1
                        LIM_SUPERIOR = 1
                        MESES = 1
                    RANGE_START = date(THIS_YEAR, THIS_MONTH, LIM_INFERIOR)
                    RANGE_ENDNG = date(
                        THIS_YEAR, THIS_MONTH, LIM_SUPERIOR
                    ) + relativedelta(months=MESES)
                # Caso cuando SEMANALES
                elif periodo.dias_imss == 7:
                    DOWK = TODAY.weekday()
                    DIFF = TODAY - relativedelta(days=DOWK)
                    RANGE_START = date(DIFF.year, DIFF.month, DIFF.day)
                    RANGE_ENDNG = RANGE_START + relativedelta(days=7)
                # Caso cuando DIARIOS
                elif periodo.dias_imss == 1:
                    RANGE_START = date(THIS_YEAR, THIS_MONTH, THIS_DAY)
                    RANGE_ENDNG = date(
                        THIS_YEAR, THIS_MONTH, THIS_DAY
                    ) + relativedelta(days=1)
                # Sin resolucion: asigna 0.
                else:
                    rec.total_dias = DIAS
                    return

            # Se realiza el 'query' filtrando segun la periodicidad.
            domain = [
                ("employee_id", "=", rec.empleado_id.id),
                ("date", ">=", RANGE_START),
                ("date", "<", RANGE_ENDNG),
            ]

            # Se realiza la cuenta de registros que satisfacen condicion.
            DIAS = rec.env["hr.attendance"].search_count(domain)
            rec.total_dias = DIAS

    # === MODELO RESTRICCIONES ===
