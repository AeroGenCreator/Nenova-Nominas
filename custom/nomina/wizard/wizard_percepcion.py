from odoo import api, fields, models


class PercepcionWizard(models.TransientModel):
    # === MODELO CONFIG ===

    _name = "percepcion.wizard"
    _description = "Agrega percepciones a la nómina."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Registro", compute="computar_nombre", store=True)
    fecha_activacion = fields.Date(
        string="Fecha Activación", default=lambda self: fields.Date.today()
    )
    nomina_id = fields.Many2one(
        string="Nómina",
        comodel_name="nomina.wizard",
        readonly=True,
        default=lambda self: self.env["nomina.wizard"].browse(
            self.env.context.get("active_id", "")
        ),
    )
    empleado_id = fields.Many2one(
        string="Empleado", comodel_name="hr.employee", required=True
    )
    percepcion = fields.Many2one(
        string="Percepción", required=True, comodel_name="nomina.percepcion"
    )
    periodicidad = fields.Many2one(
        string="Periodicidad", comodel_name="nomina.periodo.pago", required=True
    )
    monto = fields.Float(string="Monto", digits=(16, 4), required=True)
    monto_diario = fields.Float(
        string="Valor Diario",
        digits=(16, 4),
        compute="computar_monto_diario",
        store=True,
    )
    tipo = fields.Selection(
        selection=[
            ("fija", "Fija"),
            ("porcentaje.sueldo", "Porcentaje Del Sueldo"),
            ("variable", "Variable"),
        ],
        default="fija",
    )
    integra_sbc = fields.Boolean(
        string="Integra al Salario Base de Cotización (SBC)", default=True
    )
    grava_isr = fields.Boolean(
        string="Impuesto Sobre Renta (ISR)", default=False
    )
    grava_isn = fields.Boolean(
        string="Impuesto Sobre Nómina (ISN)", default=False
    )

    # === MODELO LÓGICA ===

    @api.depends("empleado_id", "percepcion", "tipo")
    def computar_nombre(self):
        for rec in self:
            NAME = False
            validate = ((rec.empleado_id), (rec.percepcion), (rec.tipo))
            if all(validate):
                SELECTION = dict(self._fields["tipo"]._selection)
                NAME = (
                    f"{rec.empleado_id.name} "
                    f"{rec.percepcion.name} - "
                    "Percepcion "
                    f"({SELECTION.get(rec.tipo, '')})"
                )
            rec.name = NAME

    @api.depends("monto", "periodicidad", "tipo")
    def computar_monto_diario(self):
        DIARIO = 0
        SELECTION = dict(self._fields["tipo"]._selection)
        for rec in self:
            validate = ((rec.monto), (rec.periodicidad), (rec.tipo))
            if all(validate):
                if SELECTION.get(rec.tipo, "") == "Fija":
                    try:
                        DIARIO = fields.Float.round(
                            (rec.monto / rec.periodicidad.dias_imss),
                            precision_rounding=4,
                        )
                    except ZeroDivisionError:
                        rec.integra_sbc = False
                        DIARIO = 0
            rec.monto_diario = DIARIO

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint(
        "UNIQUE(empleado_id, percepcion, tipo)",
        "Esta percepción ya existe en la lista.",
    )
