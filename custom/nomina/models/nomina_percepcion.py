from odoo import api, fields, models
from odoo.exceptions import ValidationError

MSG = (
    "El total calculado de importe no coincide con la "
    "suma de (gravantes y exentos)."
)


class NominaPercepcion(models.Model):
    # === MODELO CONFIG ===

    _name = "nomina.percepcion"
    _description = "Historico de Percepciones - Relacionado con Nominas"

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Percepción",
        compute="_compute_nombre",
        readonly=True,
        store=True
    )
    nomina_id = fields.Many2one(
        string="Nómina",
        comodel_name="nomina.nomina",
        ondelete="restrict",
        required=True,
        readonly=True,
    )
    concepto_id = fields.Many2one(
        string="Concepto",
        comodel_name="nomina.concepto",
        ondelete="restrict",
        required=True,
        readonly=True,
    )
    empleado_id = fields.Many2one(
        string="Empleado",
        comodel_name="hr.employee",
        related="nomina_id.empleado_id",
        store=True,
        readonly=True,
    )
    cantidad = fields.Float(
        string="Cantidad",
        default=1.0,
        digits=(16, 4),
        required=True,
        readonly=True,
        help="Cuantas unidades del concepto seran consideradas para el importe",
    )
    importe = fields.Float(
        string="Importe",
        default=0,
        digits=(16, 4),
        required=True,
        readonly=True,
        help="Valor unitario de esta percepcion",
    )
    importe_gravado = fields.Float(
        string="Importe Gravado",
        digits=(16, 4),
        default=0,
        required=True,
        readonly=True,
    )
    importe_exento = fields.Float(
        string="Importe Exento",
        digits=(16, 4),
        default=0,
        required=True,
        readonly=True,
    )
    total = fields.Float(
        string="Total",
        digits=(16, 4),
        compute="_compute_total",
        store=True,
        readonly=True,
    )
    active = fields.Boolean(string="Archivar", default=True)

    # === MODELO LÓGICA ===

    @api.depends("nomina_id.name", "concepto_id.name", "empleado_id.name")
    def _compute_nombre(self):
        for rec in self:
            NAME = False
            if rec.nomina_id and rec.concepto_id and rec.empleado_id:
                NAME = (
                    f"{rec.nomina_id.name} "
                    f"{rec.concepto_id.name} "
                    f"{rec.empleado_id.name}"
                )
            rec.name = NAME

    @api.depends("cantidad", "importe")
    def _compute_total(self):
        for rec in self:
            rec.total = fields.Float.round(
                rec.cantidad * rec.importe,
                precision_rounding=0.0001,
            )

    # === MODELO RESTRICCIONES ===

    @api.constrains("total", "importe_gravado", "importe_exento")
    def _validar_total_(self):
        for rec in self:
            IMPORTES = rec.importe_gravado + rec.importe_exento
            if round(rec.total, 4) != round(IMPORTES, 4):
                raise ValidationError(MSG)
