from odoo import fields, models


class NominaVacacionesHistorial(models.Model):

    # === MODELO CONFIG ===

    _name = "nomina.vacaciones.historial"
    _description = (
        "Congela los registros vacacionales. Genera un historial de consulta."
    )

    # === MODELO CAMPOS ===

    name = fields.Char(string="Registro", compute="", store=True)
    empleado = fields.Char(string="Empleado", required=True)
    derecho_vacacional = fields.Char(string="Derecho Vacacional", required=True)
    comienza = fields.Date(string="Comienza", required=True)
    finaliza = fields.Date(string="Finaliza", required=True)
    total_dias = fields.Integer(string="Total Días", required=True)
    anho = fields.Integer(string="Año", required=True)
    active = fields.Boolean(string="Activo", default=True)

    # === MODELO LÓGICO ===

    def cronjob_historial_vacacional(self) -> None:

        # Cargar todos los registros de vacaciones.
        vacaciones = self.env["nomina.vacaciones"].search([])
        if not vacaciones:
            return

        # Determinar registros de vacación completados.
        records_to_delete = []
        records_to_create = []

        TODAY = fields.Date.today()

        for record in vacaciones:
            if record.finaliza < TODAY:
                records_to_delete.append(record.id)
                records_to_create.append({
                    "empleado": record.empleado_id.name,
                    "derecho_vacacional": record.derecho_id.name,
                    "comienza": record.comienza,
                    "finaliza": record.finaliza,
                    "total_dias": record.dias,
                    "anho": record.anho,
                    "active":True,
                })

        # Sí registros de vacaciones completados:
        # Elminar de edición; agregar al historial.
        if records_to_create and records_to_delete:
            delete = self.env["nomina.vacaciones"].browse(records_to_delete)
            self.create(records_to_create)
            delete.unlink()
