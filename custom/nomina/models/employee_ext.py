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
        compute="",  # Agregar el computado cuando se termine la función
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

    @api.depends("")
    def computar_salario_diario_integrado(self):
        pass
