from odoo import api, fields, models

# === MENSAJES AYUDA ===

MSG_SDI = "Base de calculo para las contribuciones al IMSS"
MSG_CAT = (
    "Esta categoria puede variar segun tipo de nomina "
    "(ordinal o extraordinaria)."
)


class NominaEmployeeExt(models.Model):
    """Agregacion de campos para la construcción de nóminas"""

    # === MODELO CONFIG ===

    _inherit = "hr.employee"

    # === MODELO CAMPOS NUEVOS ===

    fecha_contratacion = fields.Date(string="Fecha Contratación")
    antiguedad_anhos = fields.Integer(
        string="Antiguedad",
        compute="computar_anhos_antiguedad",
        store=True
    )
    sueldo_bruto = fields.Float(
        string="Sueldo Bruto",
        digits=(12, 4)
    )
    periodo_pago_id = fields.Many2one(
        string="Periodicidad de Pago (Contrato)",
        help=MSG_CAT,
        comodel_name="nomina.periodo.pago",
    )
    sueldo_diario = fields.Float(
        string="Sueldo Diario (Bruto)",
        compute="computar_sueldo_diario_bruto",
        digits=(12, 4),
        readonly=True,
        store=True
    )
    """
    Sumar los días del año + días de vacaciones
    (multiplicados por la prima vacacional que por ley es del 25%)
    + días de aguinaldo.
    Después el resultado se divide entre los días del año.
    """
    salario_integral = fields.Float(
        string="Salario Diario Integrado (SDI)",
        help=MSG_SDI,
        compute="computar_salario_diario_integrado",
        digits=(12, 4),
        store=True
    )
    # No se puede eliminar la jornada si hay empleados haciendo uso de esta.
    jornada_id = fields.Many2one(
        string="Jornada", comodel_name="nomina.jornada", ondelete="restrict"
    )
    # Si se elimina plan vacacional, set a null en plan vacional.
    plan_vacacional_id = fields.Many2one(
        string="Plan Vacacional",
        comodel_name="nomina.plan.vacacional",
        ondelete="set null"
    )
    plan_percepciones_id = fields.Many2one(
        string="Plan de Percepciones",
        comodel_name="nomina.plan.percepciones",
        ondelete="set null",
    )
    prima_vacacional_factor_id = fields.Many2one(
        string="Factor (Prima Vacacional)",
        comodel_name="nomina.prima.vacacional.factor",
    )
    aguinaldo_plan_id = fields.Many2one(
        string="Aguinaldo Plan",
        comodel_name="nomina.aguinaldo.plan"
    )
    factor_integracion = fields.Float(
        string="Factor Integracion",
        digits=(16, 4),
        compute="computar_factor_integracion",
    )

    # === MODELO LÓGICA ===

    @api.depends("fecha_contratacion")
    def computar_anhos_antiguedad(self):
        """Computar años antiguedad de empleado"""
        for rec in self:
            ANHOS = False
            if rec.fecha_contratacion:
                ANHO_ACTUAL = fields.Date.today().year
                ANHO_CONTRATACION = rec.fecha_contratacion.year
                ANHOS = ANHO_ACTUAL - ANHO_CONTRATACION
            rec.antiguedad_anhos = ANHOS

    @api.depends("sueldo_bruto", "periodo_pago_id")
    def computar_sueldo_diario_bruto(self):
        """
        Unicamente muestra el sueldo bruto diario del empleado
        Su función es principalmente de referencia.
        """
        for rec in self:
            BRUTO_DIARIO = False
            validate = ((rec.sueldo_bruto), (rec.periodo_pago_id))
            if all(validate):
                BRUTO_DIARIO = rec.sueldo_bruto / rec.periodo_pago_id.dias
            rec.sueldo_diario = BRUTO_DIARIO

    @api.depends(
        "antiguedad_anhos",
        "prima_vacacional_factor_id",
        "aguinaldo_plan_id.rango_ids.dias",
        "aguinaldo_plan_id.rango_ids.limite_inferior",
        "aguinaldo_plan_id.rango_ids.limite_superior",
        "plan_vacacional_id.rango_ids.rango_id.limite_inferior",
        "plan_vacacional_id.rango_ids.rango_id.limite_superior",
        "plan_vacacional_id.rango_ids.rango_id.dias_vacaciones",
    )
    def computar_factor_integracion(self):
        for rec in self:
            FACTOR = 0
            if (
                rec.antiguedad_anhos and
                rec.plan_vacacional_id and
                rec.aguinaldo_plan_id and
                rec.prima_vacacional_factor_id
            ):

                # Singleton 'Rango Vacacional' segun antiguedad.
                record_vacaciones = rec.plan_vacacional_id.rango_ids.filtered(
                    lambda r:
                    (
                        r.rango_id.limite_inferior <=
                        rec.antiguedad_anhos <=
                        r.rango_id.limite_superior
                    )
                )[:1]

                # Si no se obtiene nada obtener el ultimo mas cercano
                if not record_vacaciones:
                    record_vacaciones = rec.plan_vacacional_id.rango_ids.sorted(
                        key=lambda r: r.rango_id.limite_superior,
                        reverse=True
                    )[:1]

                dias_vacaciones = record_vacaciones.rango_id.dias_vacaciones

                record_aguinaldo = rec.aguinaldo_plan_id.rango_ids.filtered(
                    lambda r:
                    (
                        r.limite_inferior <=
                        rec.antiguedad_anhos <=
                        r.limite_superior
                    )
                )[:1]

                if not record_aguinaldo:
                    record_aguinaldo = rec.aguinaldo_plan_id.rango_ids.sorted(
                        key=lambda r: r.limite_superior,
                        reverse=True
                    )
                FACTOR = (
                            365 + record_aguinaldo.dias +
                        (
                            dias_vacaciones *
                            rec.prima_vacacional_factor_id.factor
                        )
                    ) / 365
            rec.factor_integracion = FACTOR

    @api.depends("sueldo_diario", "factor_integracion")
    def computar_salario_diario_integrado(self):
        for rec in self:
            AMOUNT = 0
            if rec.sueldo_diario and rec.factor_integracion:
                AMOUNT = rec.sueldo_diario * rec.factor_integracion
            rec.salario_integral = AMOUNT
