from odoo import api, fields, models  # pyright: ignore
from odoo.exceptions import ValidationError  # pyright: ignore


class Contrato(models.Model):
    # === Modelo Config ===
    _name = "contrato"
    _description = "Modelo - Cada registro un contrato"

    # === Modelo Campos ===
    name = fields.Char(
        string="Nombre Del Contrato", compute="_computar_nombre_contrato_"
    )
    empleado_id = fields.Many2one(
        string="Contrato Empleado", comodel_name="hr.employee"
    )
    comienza = fields.Date(string="Contrato Inicio", required=True)
    finaliza = fields.Date(string="Contrato Finaliza", required=True)
    vigencia = fields.Integer(
        string="Dias Vigencia",
        readonly=True,
        compute="_vigencia_contrato_dias_",
    )
    active = fields.Boolean(string="Contrato Activo", default=lambda self: True)
    contrato_pdf = fields.Binary(string="PDF del contrato", required=True)

    # === Modelo Logica ===
    @api.depends("empleado_id", "comienza", "finaliza")
    def _computar_nombre_contrato_(self):
        for rec in self:
            validate = ((rec.empleado_id), (rec.comienza), (rec.finaliza))
            if all(validate):
                rec.name = (
                    f"{rec.empleado_id.name} {rec.comienza} {rec.finaliza}"
                )
            else:
                rec.name = False

    @api.depends("finaliza")
    def _vigencia_contrato_dias_(self):
        for rec in self:
            if rec.finaliza:
                TODAY = fields.Date.today()
                vigencia = rec.finaliza - TODAY
                rec.vigencia = vigencia.days
            else:
                rec.vigencia = False

    # === Modelo Restricciones ===
    @api.constrains("empleado_id")
    def _check_date_end(self):
        for rec in self:
            if rec.empleado_id:
                domain = [
                    ("empleado_id", "=", rec.empleado_id),
                    ("active", "=", True),
                    ("id", "!=", rec.ids),
                ]
                contrato = self.env["contrato"].search(domain, limit=1)
                if contrato:
                    raise ValidationError(
                        "Este empleado cuenta con un contrato activo. "
                        f"Vigencia de su contrato actual {contrato.vigencia}"
                    )
