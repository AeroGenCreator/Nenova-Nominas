from odoo import api, fields, models

MSG = (
    "Solo se puede tener un derecho vacacional por año. "
    "Si se esta forzando la creación de un registro que no se muestra "
    "es posible que el registro se encuentre archivado. "
    "El motivo es la caducidad para el derecho vacacional "
    "el cual se 'computa' a traves de la fecha oficial de "
    "contratación del empleado seleccionado."
)


class NominaDerechoVacacional(models.Model):
    """
    Este modelo no pretende ser relacional.
    Es un borrador estatico de derecho vacacional.
    Cada registro es un año.
    """

    # === MODELO CONFIG ===

    _name = "nomina.derecho.vacacional"
    _description = (
        "Registro: Derecho vacacional y caducidad del mismo por empleado."
    )

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Derecho Vacacional",
        compute="computar_nombre_registro",
        store=True,
    )
    empleado_id = fields.Many2one(
        string="Empleado", comodel_name="hr.employee", ondelete="restrict"
    )
    plan_id = fields.Many2one(
        string="Plan Vacacional",
        comodel_name="nomina.plan.vacacional",
        ondelete="restrict",
    )
    rango_id = fields.Many2one(
        string="Rango",
        comodel_name="nomina.vacacional.rangos",
        ondelete="restrict",
    )
    dias_vacaciones = fields.Integer(string="Dias Disponibles")
    cuenta_regresiva = fields.Date(string="Cuenta Regresiva", compute="")
    fecha_contratacion = fields.Date(string="Fecha Contratación")
    fecha_activacion = fields.Date(string="Fecha Activación")
    anho_activacion = fields.Integer(string="Año Activación")
    fecha_caducidad = fields.Date(string="Fecha Caducidad")
    active = fields.Boolean(
        string="Derecho Vacacional Activo",
        compute="computar_archivado",
        store=True,
    )
    vacaciones_ids = fields.One2many(
        string="Vacaciones",
        comodel_name="nomina.vacaciones",
        inverse_name="derecho_id",
    )

    # === MODELO LÓGICA ===

    @api.depends("empleado_id", "anho_activacion")
    def computar_nombre_registro(self):
        for rec in self:
            NAME = False
            if rec.empleado_id and rec.anho_activacion:
                NAME = f"{rec.empleado_id.name} {rec.anho_activacion} derecho"
            rec.name = NAME

    @api.depends("fecha_caducidad", "dias_vacaciones")
    def computar_archivado(self):
        """
        Archiva el derecho:
        Sí se supera la caducidad o se agotan los dias de vacaciones.

        Sí se supera la caducidad -> Crear un registro vacacional 'caducado'
        con los días perdidos.
        """
        for rec in self:
            BOOL = True
            TODAY = fields.Date.today()
            if rec.fecha_caducidad:
                if rec.fecha_caducidad < TODAY:
                    BOOL = False
                    self.env["nomina.vacaciones"].create({
                        "empleado_id": rec.empleado_id.id,
                        "derecho_id": rec.id,
                        "anho": rec.anho_activacion,
                        "dias_caducados": rec.dias_vacaciones
                    })
            if rec.dias_vacaciones:
                if rec.dias_vacaciones <= 0:
                    BOOL = False
            rec.active = BOOL

    # === MODELO RESTRICCIONES ===

    _validar_un_solo_derecho_por_año_ = models.Constraint(
        "UNIQUE(empleado_id, anho_activacion, plan_id)", MSG
    )
