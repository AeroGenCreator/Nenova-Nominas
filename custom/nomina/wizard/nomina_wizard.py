from odoo import fields, models


class NominaWizard(models.TransientModel):

    # === MODELO CONFIG ===

    _name = "nomina.wizard"
    _description = (
        "Almacena en buffer una nomina para el empleado "
        "desde el cual se haya disparado el evento."
    )

    # === MODELO CAMPOS ===

    name = fields.Char(string="", compute="", store=True)
    uma = fields.Many2one(string="UMA", comodel_name="nomina.uma")
    sdi = fields.Float(string="Salario Diario Integrado (SDI)", digits=(16, 4))
    sueldo = fields.Float(string="Sueldo", compute="")
    factor_riesgo_trabajo_id = fields.Many2one(
        string="Factor Riesgo de Trabajo", comodel_name="nomina.riesgo.trabajo"
    )
    percepciones_total = fields.Float(
        string="Perpeciones Total", digits=(16, 4), compute=""
    )
    percepciones_ids = fields.One2many(
        string="Perpeciones",
        comodel_name="percepcion.wizard",
        inverse_name="nomina_id",
    )
    total_dias = fields.Integer(string="Total Días")

    # === MODELO LÓGICA ===

    # === MODELO RESTRICCIONES ===
