from odoo import fields, models

UNIQUE = "Esta percepcion ya existe. Se recomienda modificar la original-"


class NominaPercepciones(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.percepciones"
    _description = "Registra todo tipo de percepciones para el calculo del SDI."

    # === MODELO CAMPOS ===

    name = fields.Char(string="Percepción Nombre", required=True)
    periodicidad = fields.Many2one(
        string="Periodicidad",
        comodel_name="nomina.periodo.pago"
    )
    monto = fields.Float(
        string="Monto",
        digits=(16,4)
    )
    tipo_de_calculo = fields.Selection(
        selection=[
            ("fijo", "Fijo"),
            ("porcentaje/sueldo", "Porcentaje Del Sueldo"),
            ("manual", "Manual"),
            ("formula", "Fórmula"),
        ],
        default="fijo"
    )
    condicion = fields.Many2one(
        string="Condición de la percepcion",
        comodel_name="nomina.condicion.percepcion",
        ondelete="restrict",
    )
    integra_sdi = fields.Boolean(
        string="Esta percepción Integra al SDI",
        default=False,
    )
    grava_isr = fields.Boolean(
        string="Cuenta para el ISR",
        default=False,
    )
    grava_imss = fields.Boolean(
        string="Cuenta para el IMSS",
        default=False,
    )
    grava_isn = fields.Boolean(
        string="Cuenta para el ISN",
        default=False,
    )
    active = fields.Boolean(string="Registro Activo", default=True)

    # === MODELO LÓGICA ===

    # === MODELO RESTRICCIONES ===
    _unicos_ = models.Constraint(
        (
            "UNIQUE(name, periodicidad, tipo_de_calculo, "
            "condicion, integra_sdi, grava_isr, grava_imss, grava_isn)"
        ),
        UNIQUE
    )
