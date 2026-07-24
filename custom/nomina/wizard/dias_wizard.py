from odoo import api, fields, models
from odoo.exceptions import ValidationError

RANGO_INVALIDO = "Rango de horas invalido para la creación de registro."


class NominaDiasWizard(models.TransientModel):
    """
    Este wizards se dispara cuando se require llenar una jornada de días
    de manera eficiente sin tener que hacer el ingreso manual.
    """

    # === MODELO CONFIG ===

    _name = "nomina.dias.wizard"
    _description = (
        "Genera los registros de días para una jornada de manera automática"
    )

    # === MODELO CAMPOS ===

    dia = fields.Many2many(
        string="Dias por generar",
        comodel_name="nomina.dias",
        required=True,
    )
    hora_inicio = fields.Float(string="Hora Inicio", required=True)
    hora_termino = fields.Float(string="Hora Termino", required=True)

    # === MODELO LÓGICA ===

    def action_generar_dias(self) -> None:
        """
        Construir lineas de horarios para
        la jornada actual de manera automática.
        """

        # Accion individual - Solo en el registro donde es llamada.
        self.ensure_one()

        # Extracción "id". Guardado en (self.env.context)
        record_id = self.env.context.get("active_id", "")

        # Si no hay "id" padre. Cerrar wizard.
        if not record_id:
            return {'type': 'ir.actions.act_window_close'}

        # Obtencion del recordset del padre.
        singleton = self.env["nomina.jornada"].browse(record_id)

        # Si hay dias en el padre. Eliminar
        if singleton.dia_ids:
            singleton.dia_ids.unlink()

        # Iterar los dias del wizard. Creaciond e registros. (jornada - dia)
        dias = self.dia
        vals = []
        for dia in dias:
            vals.append({
                "dia_id": dia.id,
                "hora_inicio": self.hora_inicio,
                "hora_termino": self.hora_termino,
                "active": True,
                "jornada_id": record_id
            })

        # Inyección de datos.
        self.env["nomina.dia.hora.linea"].create(vals)

    # === MODELO RESTRICCIÓN ===

    @api.constrains("hora_inicio", "hora_termino")
    def _validar_rangos_horas(self):
        MIN_LIM = 0
        MAX_LIM = 24
        for rec in self:
            is_data = ((rec.hora_inicio), (rec.hora_termino))
            if all(is_data):
                validate = (
                    (rec.hora_inicio < MIN_LIM),
                    (rec.hora_termino > MAX_LIM),
                    (rec.hora_inicio > rec.hora_termino),
                )
                if any(validate):
                    raise ValidationError(RANGO_INVALIDO)
