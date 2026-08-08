from odoo import api, fields, models


class PercepcionWizard(models.TransientModel):
    # === MODELO CONFIG ===

    _name = "percepcion.wizard"
    _description = "Agrega percepciones a la nómina."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Registro", compute="computar_nombre", store=True)
    nomina_id = fields.Many2one(string="Nómina", comodel_name="nomina.wizard")
    empleado_id = fields.Many2one(
        string="Empleado", comodel_name="hr.employee", required=True
    )
    percepcion = fields.Many2one(
        string="Percepción", required=True, comodel_name="nomina.percepciones"
    )
    periodicidad = fields.Many2one(
        string="Periodicidad", comodel_name="nomina.periodo.pago", required=True
    )
    monto = fields.Float(string="Monto", digits=(16, 4), required=True)
    monto_diario = fields.Float(
        string="Monto Diario de la Percepcion", digits=(16, 4), compute=""
    )
    tipo = fields.Selection(
        selection=[
            ("fijo", "Fijo"),
            ("porcentaje.sueldo", "Porcentaje Del Sueldo"),
            ("variable", "Variable"),
        ],
        default="fijo",
    )
    integra_sbc = fields.Boolean(string="Integra al SBC", default=True)
    grava_isr = fields.Boolean(string="Aplica ISR", default=False)
    grava_imss = fields.Boolean(string="Aplica IMSS", default=False)
    grava_isn = fields.Boolean(string="Aplica ISN", default=False)
    fecha_activacion = fields.Date(
        string="Fecha Activación", default=lambda self: fields.Date.today()
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

    @api.depends("montoo", "periodicidad", "tipo")
    def computar_monto_diario(self):
        pass

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint(
        "UNIQUE(empleado_id, percepcion, tipo)",
        "Esta percepción ya existe en la lista.",
    )
