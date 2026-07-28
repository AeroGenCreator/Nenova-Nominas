from odoo import fields, models


class NominaCondicionPercepcion(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.condicion.percepcion"
    _description = (
        "Categoriza las posibles condiciones para asignar percepciones. "
        "Estas condiciones las usare para declarar funciones en 'cron' "
        "para asignar tickets de percepcion."
    )

    # === MODELO CAMPOS ===

    name = fields.Char(string="Condición", required=True)
    descripcion = fields.Text(string="Descripción", required=True)
    active = fields.Boolean(string="Registro Activo", default=True)

    # === MODELO LÓGICA ===

    # === MODELO RESTRICCIONES ===
    _unique_ = models.Constraint(
        "UNIQUE(name)", "Ya existe esta condición."
    )
