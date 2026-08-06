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
    sueldo = fields.Float(string="Sueldo", compute="computar_sueldo")
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
        string="Total Días", default=lambda self: self.computar_total_dias()
    )
    percepciones_total = fields.Float(
        string="Perpeciones Monto Total", digits=(16, 4), compute=""
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
                NAME = f"Borrador Nómina de {rec.empleado_id.name}"
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

    def computar_total_dias(self):
        """ Automático: Busca asistencias o regresa 0."""
        DIAS = 0
        if self.periodicidad and self.empleado_id:
            p_domain = [("name","=",self.periodicidad)]
            periodo = self.env["nomina.periodo.pago"].search(p_domain)
            if periodo:
                TODAY = fields.Date.today()
                THIS_MONTH = TODAY.month
                THIS_YEAR = TODAY.year
                THIS_DAY = TODAY.day
                if periodo.dias_imss > 30:
                    MESES = (periodo.dias_imss // 30) - 1
                    RANGE_START = (
                        date(THIS_YEAR, THIS_MONTH, 1) - relativedelta(
                            months=MESES
                        )
                    )
                    RANGE_ENDNG = (
                        date(THIS_YEAR, THIS_MONTH, 1) + relativedelta(months=1)
                    )
                elif periodo.dias_imss == 30:
                    RANGE_START = date(THIS_YEAR, THIS_MONTH, 1)
                    RANGE_ENDNG = (
                        date(THIS_YEAR, THIS_MONTH, 1) + relativedelta(months=1)
                    )
                elif periodo.dias_imss < 30:
                    if periodo.dias_imss in (15, 14):
                        MESES = 0
                        LIM_INFERIOR = 1
                        LIM_SUPERIOR = periodo.dias_imss + 1
                        if THIS_DAY > periodo.dias_imss:
                            LIM_INFERIOR = periodo.dias_imss + 1
                            LIM_SUPERIOR = 1
                            MESES = 1
                        RANGE_START = date()
                        RANGE_ENDNG = date()
                    elif periodo.dias_imss == 7:
                        pass
                    elif periodo.dias_imss == 1:
                        pass
                    else:
                        return DIAS
                else:
                    return DIAS
                domain = [
                    ("employee_id", "=", self.empleado_id),
                    ("date", ">=", RANGE_START),
                    ("date", "<", RANGE_ENDNG),
                ]
                DIAS = self.env["hr.attendance"].search_count(domain)
        return DIAS

    # === MODELO RESTRICCIONES ===
