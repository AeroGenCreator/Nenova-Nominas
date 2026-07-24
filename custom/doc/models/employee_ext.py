from odoo import fields, models  # pyright: ignore


class EmpEmployeeExt(models.Model):
    # === Modelo Config ===
    _inherit = "hr.employee"

    # === Modelo Campos Nuevos ===
    contrato_ids = fields.One2many(
        string="Contratos", comodel_name="contrato", inverse_name="empleado_id"
    )
    documento_ids = fields.One2many(
        string="Documentos", comodel_name="documento", inverse_name="empleado_id"
    )
