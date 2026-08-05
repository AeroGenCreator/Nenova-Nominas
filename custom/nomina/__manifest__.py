# -*- coding: utf-8 -*-
{
    "name": "Nominas Empleados",  # pyright: ignore
    "summary": "Modulo: Agrega salarios, beneficios y deducciones.",
    "description": """
        Permite administrar las nominas de empleados.
        Extiende modelo de empleados.
        Agrega nuevas vistas para manejo de nominas.
        Deducciones y Prestaciones.
        (Vacaciones, Utilidades, Aguinaldos, Finiquito.)
        """,
    "author": "Andrés Alberto López Mendoza / Nentria",
    "website": "https://github.com/AeroGenCreator",
    "category": "uncategorized",
    "version": "0.1",
    "depends": ["hr"],
    "data": [
        "security/ir.model.access.csv",
        "data/nomina.prima.vacacional.factor.csv",
        "data/nomina.riesgo.trabajo.csv",
        "data/nomina.aguinaldo.categoria.csv",
        "data/nomina.aguinaldo.rangos.csv",
        "data/nomina.plan.vacacional.csv",
        "data/nomina.vacacional.categoria.csv",
        "data/nomina.vacacional.rangos.csv",
        "data/nomina.plan.rango.rel.csv",
        "data/nomina.periodo.pago.csv",
        "data/nomina.dias.csv",
        "data/nomina.uma.csv",
        "views/plan_percepciones_empleado_wizard.xml",
        "views/aguinaldo_plan.xml",
        "views/aguinaldo_rangos.xml",
        "views/cronjob_vacaciones.xml",
        "views/aguinaldo_categoria.xml",
        "views/vacaciones_historial.xml",
        "views/condicion_percepcion.xml",
        "views/prima_vacacional_factor.xml",
        "views/factor_riesgo_trabajo.xml",
        "views/vacacional_categoria.xml",
        "views/plan_empleado_wizard.xml",
        "views/derecho_vacacional.xml",
        "views/plan_rangos_wizard.xml",
        "views/plan_percepciones.xml",
        "views/vacacional_rangos.xml",
        "views/empleados_wizard.xml",
        "views/plan_vacacional.xml",
        "views/dia_hora_linea.xml",
        "views/employee_ext.xml",
        "views/percepciones.xml",
        "views/periodo_pago.xml",
        "views/dias_wizard.xml",
        "views/vacaciones.xml",
        "views/main_view.xml",
        "views/jornada.xml",
        "views/uma.xml",
        "views/menu.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "assets": {
        "web.assets_backend": [
            "nomina/static/src/js/custom_monetary_float.js"
        ],
    },
}
