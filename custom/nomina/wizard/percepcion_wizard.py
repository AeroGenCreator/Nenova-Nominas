from odoo import api, fields, models


class PercepcionWizard(models.TransientModel):

    # === MODELO CONFIG ===

    _name = "percepcion.wizard"
    _description = "Agrega percepciones a la nómina."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Registro", compute="", store=True)
    empleado_id = fields.Many2one(string="Empleado", comodel_name="hr.employee")
    percepcion = fields.Many2one(
        string="Percepción", required=True, comodel_name="nomina.percepciones"
    )
    periodicidad = fields.Many2one(
        string="Periodicidad", comodel_name="nomina.periodo.pago", required=True
    )
    monto = fields.Float(string="Monto", digits=(16, 4), required=True)
    tipo = fields.Selection(
        selection=[
            ("fijo", "Fijo"),
            ("porcentaje.sueldo", "Porcentaje Del Sueldo"),
        ],
        default="fijo",
    )
    integra_sdi = fields.Boolean(string="Integra al SDI", default=True)
    grava_isr = fields.Boolean(string="Aplica ISR", default=False)
    grava_imss = fields.Boolean(string="Aplica IMSS", default=False)
    grava_isn = fields.Boolean(string="Aplica ISN", default=False)
    fecha_activacion = fields.Date(
        string="Fecha Activación", default=lambda self: fields.Date.today()
    )
    nomina_id = fields.Many2one(
        string="Nómina", comodel_name="nomina.wizard"
    )

    # === MODELO LÓGICA ===

    @api.depends("empleado_id", "percepcion", "tipo")
    def computar_nombre(self):
        for rec in self:
            NAME = False
            validate = ((rec.empleado_id), (rec.percepcion), (rec.tipo))
            if all(validate):
                NAME = f"{rec.empleado_id} {rec.percepcion} {rec.tipo}"
            rec.name = NAME

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint(
        "UNIQUE(empleado_id, percepcion, tipo)",
        "Esta percepción ya existe en la lista.",
    )
