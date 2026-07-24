import random
import string

from odoo import fields, models  # pyright: ignore

CHARACTERS = string.ascii_letters + string.digits
PASSWORD_LENGTH = 10


class NenPlaEmployeeExt(models.Model):
    # === Modelo: config ===
    _inherit = "hr.employee"

    # === Modelo: Campos Nuevos ===
    contraseña_portal = fields.Char(
        string="Contraseña Portal", readonly=True, default=False
    )

    # === Modelo: Logica ===
    def generar_contraseña(self):
        for rec in self:
            selections = []
            for i in range(1, PASSWORD_LENGTH, 1):
                char = random.choice(CHARACTERS)
                selections.append(char)
            rec.contraseña_portal = "".join(selections)
