from odoo import fields, models


class NominaNominaWizard(models.TransientModel):
    _name = "nomina.nomina.wizard"
    _description = (
        "Almacena en buffer una nomina para el empleado "
        "desde el cual se haya disparado el evento."
    )

    name = fields.Char(string="", compute="", store=True)
    uma = fields.Many2one(
        string="UMA", comodel_name="nomina.uma"
    )
    sdi = fields.Float(string="Salario Diario Integrado (SDI)", digits=(16, 4))
    sueldo = fields.Float(string="Sueldo", compute="")
    factor_riesgo_trabajo = fields.Many2one(
        string="Factor Riesgo de Trabajo", comodel_name="nomina.riesgo.riesgo"
    )  # Nuevo Modelo
    percepciones_total = fields.Float(
        string="Perpeciones Total", digits=(16, 4)
    )
    percepciones_ids = fields.One2many(
        string="Perpeciones", comodel_name="nomina.percepcion.activa"
    )  # Nuevo Modelo

    def action_agregar_percepciones_activas(self):
        pass
