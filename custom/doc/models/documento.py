from odoo import api, fields, models  # pyright: ignore


class Documento(models.Model):
    # === Modelo config ===
    _name = "documento"
    _description = "Modelo - Cada registro un documento"

    # === Modelo Campos ===
    name = fields.Char(
        string="Nombre Del Registro", compute="_computar_nombre_documento_"
    )
    empleado_id = fields.Many2one(string="Empleado", comodel_name="hr.employee")
    fecha = fields.Date(
        string="Fecha de carga",
        default=lambda self: fields.Date.today(),
        readonly=True,
    )
    documento_tipo_id = fields.Many2one(
        string="Documento Tipo", comodel_name="documento.tipo"
    )
    active = fields.Boolean(
        string="Documento Activo", default=lambda self: True
    )
    documento_pdf = fields.Binary(string="Documento", required=True)

    # === Modelo Logica ===
    # Computar nombre del registro
    @api.depends("empleado_id", "documento_tipo_id")
    def _computar_nombre_documento_(self):
        for rec in self:
            validate = ((rec.empleado_id), (rec.documento_tipo_id))
            if all(validate):
                rec.name = (
                    f"{rec.empleado_id.name} {rec.documento_tipo_id.name}"
                )
            else:
                rec.name = False

    # === Modelo Restricciones ===
    _validar_un_tipo_por_empleado_ = models.Constraint(
        "UNIQUE(empleado_id, documento_tipo_id)",
        "Solo se requiere de un tipo documento por empleado.",
    )
