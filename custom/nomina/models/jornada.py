from odoo import api, fields, models


class NominaJornada(models.Model):
    """
    Este modelo crea registros 'Jornadas'.
    Uniendo:
    (
        Tipo de turno, descanso, horarios='Dias-Inicio-Termino', Empleados,
        hr. Totales
    )
    Responde -> Qué empleados tienen esta jornada?
    Responde -> Qué horarios tiene esta jornada?
    Responde -> Cuántas horas totales se cumplen en esta jornada?
    Responde -> Tipo de turno para esta jornada.
    Responde -> Tiempo 'descanso' descuento al contador de asitencia. (Jornada)
    """

    # === MODELO CONFIG ===

    _name = "nomina.jornada"
    _description = "Permite: construcción personalizada de jornadas laborales"

    # === MODELO CAMPOS ===

    name = fields.Char(
        string="Jornada", compute="computar_nombre_jornada", store=True
    )
    alias = fields.Char(string="Alias", required=True)
    turno = fields.Selection(
        string="Turno",
        required=True,
        selection=[
            ("diurna", "Diurna"),
            ("nocturna", "Nocturna"),
            ("mixta", "Mixta"),
        ],
    )
    total_empleados = fields.Integer(
        string="Total Empleados",
        compute="computar_total_empleados",
        store=True,
        readonly=True
    )
    descanso = fields.Float(string="Tiempo (Descanso Diario)")
    horas_totales = fields.Float(
        string="Horas Totales (Esta Jornada)",
        compute="computar_total_horas",
        readonly=True,
        digits=(5, 2),
    )
    active = fields.Boolean(string="Activo", default=True)
    empleado_ids = fields.One2many(
        string="Empleados",
        comodel_name="hr.employee",
        inverse_name="jornada_id",
    )
    dia_ids = fields.One2many(
        string="Horario (dias - horas)",
        comodel_name="nomina.dia.hora.linea",
        inverse_name="jornada_id",
    )

    # === MODELO LÓGICA ===

    @api.depends("turno", "alias")
    def computar_nombre_jornada(self):
        for rec in self:
            NAME = False
            validate = (
                (rec.alias),
                (rec.turno),
            )
            if all(validate):
                dicc = dict(self._fields["turno"].selection)
                NAME = f"{rec.alias} {dicc.get(rec.turno)}"
            rec.name = NAME

    @api.depends("empleado_ids")
    def computar_total_empleados(self):
        for rec in self:
            TOTAL = 0
            if rec.empleado_ids:
                TOTAL = len(rec.empleado_ids)
            rec.total_empleados = TOTAL

    @api.depends("descanso", "dia_ids")
    def computar_total_horas(self):
        for rec in self:
            TOTAL = 0
            if rec.dia_ids:
                for dia in rec.dia_ids:
                    if dia.estatus != "descanso":
                        TOTAL += (
                            dia.hora_termino - (dia.hora_inicio + rec.descanso)
                        )
            rec.horas_totales = TOTAL

    # === MODELO RESTRICCIONES ===

    # El modelo 'nomina.dias' restringe días repetidos para el modelo actual.
