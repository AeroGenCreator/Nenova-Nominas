from odoo import fields, models

UNIQUE = "Esta percepcion ya existe. Se recomienda modificar la original-"


class NominaPercepciones(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.percepciones"
    _description = "Registra todo tipo de percepciones para el calculo del SDI."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Percepción Nombre", required=True)
    tipo = fields.Selection(
        string="Tipo",
        selection=[
            ("exento", "Exento"),
            ("gravada", "Gravada"),
        ],
        default="exento"
    )
    tipo_de_flujo = fields.Selection(
        string="Tipo de Flujo",
        selection=[
            ("fijo", "Fijo"),
            ("variable", "Variable")
        ],
        default="fijo",
    )
    periodicidad = fields.Many2one(
        string="Periodicidad",
        comodel_name="nomina.periodo.pago"
    )
    es_fija = fields.Boolean(
        string="Es percepcion fija",
        default=True,
        help=(
            "Activar sí se desea ingresar una cantidad "
            "fija para esta percepcion."
        )
    )
    cantidad_fija = fields.Float(
        string="Percepcion",
        digits=(16,4)
    )
    condicion = fields.Many2one(
        string="Condición de la percepcion",
        comodel_name="nomina.condicion.percepcion",
        ondelete="restrict",
    )
    active = fields.Boolean(string="Registro Activo", default=True)

    # === MODELO LÓGICA ===

    # === MODELO RESTRICCIONES ===
    _unicos_ = models.Constraint(
        "UNIQUE(name, tipo, tipo_de_flujo, periodicidad, es_fija, condicion)",
        UNIQUE
    )