from odoo import fields, models


class EmpleadosWizard(models.TransientModel):

    # === MODELO CONFIG ===

    _name = "nomina.empleados.wizard"
    _description = (
        "Permite seleccionar empleados por agregar a jornada "
        "que haya disparado este evento."
    )

    # === MODELO CAMPOS ===

    empleado_ids = fields.Many2many(
        string="Empleados",
        comodel_name="hr.employee"
    )

    # === MODELO LÓGICA ===

    def action_agregar_empleados(self) -> None:
        """
        Debido a la limitante de One2many para renderizar la selección
        directa de lineas existentes de algún otro modelo.

        Se opto por este pop-up y la acción presente:

        Relaciona el Many2one de 'jornada_id' de los empleados seleccionados
        en el pop-up con el 'id' de la jornada padre que disparo este evento.
        Resolviendo así la agregación de empleados a jornadas sin
        pasar por el formulario de 'creación' predefinido de la relacion
        One2many.
        """

        # Garantizar esta accion 1 por registro.
        self.ensure_one()

        # 'ID' - Recordset del padre de este evento.
        parent_id = self.env.context.get("active_id", "")

        # Si no existe el 'ID' padre. Cerrar ventana.
        if not parent_id:
            return {'type': 'ir.actions.act_window_close'}

        SELECCIONES = self.empleado_ids
        for empleado in SELECCIONES:
            empleado.write(
                {"jornada_id": parent_id}
            )
