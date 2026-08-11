from odoo import api, fields, models


class PercepcionWizard(models.TransientModel):
    # === MODELO CONFIG ===

    _name = "percepcion.wizard"
    _description = "Agrega percepciones a la nómina."

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Percepción",
        compute="_compute_nombre",
        store=True,
        readonly=True,
    )
    nomina_id = fields.Many2one(
        string="Nómina",
        comodel_name="nomina.wizard",
        required=False,
        readonly=True,
        ondelete="restrict",
        default=lambda self: self.env.browse(
            self.env.context.get("active_id", "")
        ),
    )
    concepto_id = fields.Many2one(
        string="Concepto",
        comodel_name="nomina.concepto",
        required=True,
        ondelete="restrict",
    )
    empleado_id = fields.Many2one(
        string="Empleado",
        comodel_name="hr.employee",
        related="nomina_id.empleado_id",
        store=True,
        ondelete="restrict",
    )
    cantidad = fields.Float(
        string="Cantidad",
        compute="_compute_cantidad",
        digits=(16, 4),
        required=True,
        readonly=False,
        help="Unidades del concepto por ser evaluadas para el importe",
        store=True,
    )
    importe = fields.Float(
        string="Importe",
        compute="_compute_importe",
        digits=(16, 4),
        required=True,
        readonly=False,
        help="Valor unitario de esta percepcion",
        store=True,
    )
    total = fields.Float(
        string="Total",
        digits=(16, 4),
        compute="_compute_total",
        store=True,
        readonly=True,
    )

    # === MODELO LÓGICA ===

    @api.depends("concepto_id", "empleado_id")
    def _compute_nombre(self):
        for rec in self:
            NAME = False
            if rec.concepto_id and rec.empleado_id:
                NAME = f"{rec.concepto_id.name} {rec.empleado_id.name}"
            rec.name = NAME

    @api.depends("nomina_id","concepto_id")
    def _compute_cantidad(self):
        """
        Si la percepcion es sueldo,
        se agregan los dias del rando seleccionado desde la nomina wizard
        """
        for rec in self:
            if rec.concepto_id:
                if rec.concepto_id.codigo == "SUELDO":
                    if rec.nomina_id.rango_seleccionado:
                        CANTIDAD = rec.nomina_id.rango_seleccionado
                        rec.cantidad = CANTIDAD
                    else:
                        rec.cantidad = 1.0
                else:
                    if rec.cantidad:
                        return
                    if not rec.cantidad:
                        rec.cantidad = 1.0

    @api.depends("empleado_id", "concepto_id")
    def _compute_importe(self):
        for rec in self:
            if rec.concepto_id:
                if rec.concepto_id.codigo == "SUELDO":
                    if rec.empleado_id.sueldo_diario:
                        IMPORTE = rec.empleado_id.sueldo_diario
                        rec.importe = IMPORTE
                    else:
                        rec.importe = 0
                else:
                    if rec.importe:
                        return
                    if not rec.importe:
                        rec.importe = 0

    @api.depends("cantidad", "importe")
    def _compute_total(self):
        for rec in self:
            rec.total = fields.Float.round(
                rec.cantidad * rec.importe,
                precision_rounding=0.0001,
            )

    # === MODELO RESTRICCIONES ===

    _unicos_ = models.Constraint(
        "UNIQUE(name, nomina_id)", "Esta percepción ya existe en la nómina."
    )
