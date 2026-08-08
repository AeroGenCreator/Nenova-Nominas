from odoo import fields, models


class NominaPercepcionHistorial(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.percepcion.historial"
    _description = "Historial De Percepciones"

    # === MODELO CAMPOS ===

    name = fields.Char(string="Registro", compute="", store=True)
    percepcion = fields.Char(string="Percepción")
    empleado = fields.Char(string="Empleado")
    plan_percepcion = fields.Char(string="Plan Percepción")
    periodicidad = fields.Char(string="Periodicidad")
    fecha_creacion = fields.Date(string="Fecha Creación")
    monto = fields.Float(string="Monto", digits=(16, 4))
    integra_sbc = fields.Boolean(string="Integra al SBC", readonly=True)
    grava_isr = fields.Boolean(string="Cuenta para el ISR", readonly=False)
    grava_imss = fields.Boolean(string="Cuenta para el IMSS", readonly=False)
    grava_isn = fields.Boolean(string="Cuenta para el ISN", readonly=False)
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LÓGICA ===

    # === MODELO RESTRICCIONES ===
