from dataclasses import asdict, dataclass

from dateutil.relativedelta import relativedelta
from odoo import fields, models


@dataclass(init=True)
class PossibleRight:
    empleado_id: int
    plan_id: int
    rango_id: int
    dias_vacaciones: int
    anho_activacion: int
    fecha_contratacion: fields.Date
    fecha_activacion: fields.Date
    fecha_caducidad: fields.Date

    def to_dict(self):
        return asdict(self)


class NominaMainView(models.TransientModel):
    _name = "nomina.main.view"
    _description = (
        "Este modelo permite renderizar una main "
        "view estilo dashboard para el modulo nómina."
    )

    name = fields.Char(string="Nominas", default="Nenova")
    welcome = fields.Char(
        string="Sistema", readonly=True, default="Nenova Nóminas"
    )

    def action_refrescar_derecho_vacacional(self) -> None:
        """
        Actualiza los Registros (Derechos Vacacionales)

        Dispara evento a traves de boton en GUI o con CRON cada 00:00 cada día.
        """

        # Recordset (Empleados & Derechos)
        empleados = self.env["hr.employee"].search([])
        derechos = self.env["nomina.derecho.vacacional"].search([])

        # Lista: Cada elemento es un "empleado".
        # [{"empleado": [dicc, dicc, dicc ... ] ... ]
        possible_right = []
        for empleado in empleados:

            # Cada empelado un "diccionario".
            this_empleado = {empleado.name: []}

            # Saltar empleado sí no hay "plan vacacional".
            if not empleado.plan_vacacional_id:
                continue

            # Plan vacacional del empelado actual
            plan = empleado.plan_vacacional_id

            # Minimo años para "Derecho Vacacionl"
            minimo = sorted(
                plan.rango_ids,
                key=lambda r: r.rango_id.limite_inferior,
                reverse=False,
            )[:1]

            # Asegurar que no haya indexError
            resta = 0
            if minimo:
                resta = minimo[0].rango_id.limite_inferior

            # En caso derechos activos (todos). (Itera todos exacto).
            antiguedad_compuesto = empleado.antiguedad_anhos - resta

            # Constante (En Cálculos)
            TODAY = fields.Date.today()
            # Variable (En Cálculo)
            THIS_YEAR = TODAY.year

            # Cálculo:
            # Determinar derechos (Basado en: Aniversarios)
            # Sí Aniversario < HOY < Caducidad(este aniversario):
            # "Crear derecho" -> Disminuir Año actual en 1 -> Repetir.
            # De lo contrario: Romper "loop" siguiente "empleado".
            for cycle in range(1, antiguedad_compuesto + 1, 1):

                # Creación del Aniversario.
                anniversary = empleado.fecha_contratacion.replace(
                    year=THIS_YEAR
                )

                # Construir: Caducidad(este aniversario).
                expiration_year = THIS_YEAR + plan.caduca_anhos
                expiration_month = anniversary + relativedelta(
                    month=plan.caduca_meses
                )
                expiration_day = anniversary + relativedelta(
                    day=plan.caduca_dias
                )
                expiration = anniversary.replace(
                    year=expiration_year,
                    month=expiration_month.month,
                    day=expiration_day.day,
                )

                if anniversary <= TODAY and expiration >= TODAY:

                    # Antiguedad de este ciclo.
                    antiguedad = (
                        anniversary.year - empleado.fecha_contratacion.year
                    )

                    # Fetch: Singleton(Rango Vacacional).
                    # Basado(Antiguedad de este ciclo).
                    rango = plan.rango_ids.filtered(
                        (
                            lambda r:
                            (
                                r
                                .rango_id
                                .limite_inferior <= antiguedad <= r
                                .rango_id
                                .limite_superior
                            )
                        )
                    )[:1]

                    # Si no existe coincidencia en los rangos.
                    # Devuelve el rango con limite superior mas alto.
                    if not rango:
                        rango = plan.rango_ids.sorted(
                            key=lambda r: r.rango_id.limite_superior,
                            reverse=True
                        )[:1]

                    # Valores: Posible Derecho Vacacional.
                    kwargs = {
                        "empleado_id": empleado.id,
                        "plan_id": plan.id,
                        "rango_id": rango.rango_id.id,
                        "dias_vacaciones": rango.rango_id.dias_vacaciones,
                        "anho_activacion": THIS_YEAR,
                        "fecha_contratacion": empleado.fecha_contratacion,
                        "fecha_activacion": anniversary,
                        "fecha_caducidad":expiration
                    }

                    # Instanciar - Permitiendo el acceso como atributos.
                    model = PossibleRight(**kwargs)

                    # Se guarda en buffer.
                    this_empleado[empleado.name].append(model)

                    # Disminuir contador, repetir loop.
                    THIS_YEAR -= 1

                # De lo contrario: Siguiente empleado.
                else:
                    break

            # Guardar Empleado Iterado.
            possible_right.append(this_empleado)

        # Almacena los valores que seran creados
        vals_to_create = []
        # Almacena los valores que seran descartados
        vals_to_delete = []

        # Iterar cada epmleado con derechos.
        for empleado in possible_right:
            # Se itera su array de modelos[PossibleRight].
            for name, array in empleado.items():

                # Derechos Vacacionales(Recordsets)
                recordsets = derechos.filtered(
                    lambda r: r.empleado_id.name == name and r.active
                )

                # Se compara con registros activos.
                # Sí no hay registros activos -> Crear derechos(Ya validados)
                if not recordsets:
                    vals_to_create.extend(
                        [model.to_dict() for model in array]
                    )
                    continue

                # Sí plan vacacional cambió; Posibles records duplicados.
                # Eliminar antiguos & agregar todos los nuevos.
                if array and recordsets:
                    if array[0].plan_id != recordsets[0].plan_id.id:
                        vals_to_create.extend(
                            [model.to_dict() for model in array]
                        )
                        vals_to_delete.extend(recordsets)
                        continue

                # Sí (mismo plan) & (mismo largo) array & buffer[PossibleRight]
                # Saltar al siguiente empleado.
                if len(array) == len(recordsets):
                    # Validar que no hayan cambiado los rangos vacacionales.
                    for record in array:
                        for singleton in recordsets:
                            # Alinear - RecordNuevo = RecordAntiguo
                            # Evaluar si ya se descontaron dias de vacaciones.
                            # No se pueden alterar
                            restrict = (
                                (
                                    singleton.
                                    fecha_activacion == record.
                                    fecha_activacion
                                ),
                                (
                                    singleton.
                                    dias_vacaciones != record.
                                    dias_vacaciones
                                )
                            )
                            if all(restrict):
                                continue
                            # Evaluar Alineacion pero cambios en rangos.
                            validate = (
                                (
                                    singleton.
                                    fecha_activacion == record.
                                    fecha_activacion
                                ),
                                (
                                    singleton.
                                    rango_id.id != record.
                                    rango_id
                                )
                            )
                            if all(validate):
                                vals_to_create.append(record)
                                vals_to_delete.append(singleton)
                    # No hay rangos alterados. Si: (mismo plan) & (mismo largo)
                    # Saltar al siguiente empleado.
                    continue

                # Sí ninguna anterior:
                # Iterar registros, comparar ausentes
                # Sí ausensia:
                # Agregar diccionario de valores -> [Lista de Creación]
                for record in array:
                    for singleton in recordsets:
                        validate = (
                            (
                                singleton.
                                fecha_activacion == record.
                                fecha_activacion
                            )
                        )
                        if validate:
                            continue
                        else:
                            vals_to_create.append(record.to_dict())

        # Sí existe data(Crear Registros)
        if vals_to_create:
            self.env["nomina.derecho.vacacional"].create(vals_to_create)
        # Si hubo cambios plan vacacional(Eliminar Duplicados)
        if vals_to_delete:
            # Unir los derechos vacacionales duplicados
            derechos_desperdicio = sum(
                vals_to_delete,
                self.env["nomina.derecho.vacacional"].browse()
            )

            derechos_desperdicio.unlink()


    def action_nominas_borrador(self):
        pass
