from odoo import fields, models


class NominaPeriodoPago(models.Model):
    """
    Este modelo permite edición segun cambien las categorias.
    Sin embargo se pre-cargan datos oficiales
    al iniciar la instancia de odoo desde 'nomina.csv/nomina.periodo.pago.csv'.
    """
    # === MODELO CONFIG ===
    _name="nomina.periodo.pago"
    _description = (
        "Almacena las categorios de "
        "'Periodicidad de Pago' oficiales "
        "así como las claves y los días que cuenta cada una."
    )

    # === MODELO CAMPOS ===
    name = fields.Char(string="Periodicidad")
    clave = fields.Char(string="Clave Oficial")
    dias = fields.Float(string="Numero de días", digits=(5, 2))
    dias_imss = fields.Integer(string="Numero de días IMSS")
    active = fields.Boolean(string="Categoria Activa", default=True)
