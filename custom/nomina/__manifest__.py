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
    "depends": ["hr"], # Importante "hr.attendance" -> Instalar Manual
    "data": [
        "security/ir.model.access.csv",
        "data/nomina.concepto.csv",
        "data/nomina.prima.vacacional.factor.csv",
        "data/nomina.riesgo.trabajo.csv",
        "data/nomina.aguinaldo.categoria.csv",
        "data/nomina.aguinaldo.rangos.csv",
        "data/nomina.plan.vacacional.csv",
        "data/nomina.vacacional.categoria.csv",
        "data/nomina.vacacional.rangos.csv",
        "data/nomina.plan.rango.rel.csv",
        "data/nomina.periodo.pago.csv",
        "data/sequence_data.xml",
        "data/nomina.dias.csv",
        "data/nomina.uma.csv",
        "data/nomina.tabla.isr.csv",
        "data/nomina.tabla.subsidio.csv",
        "views/wizard_vacacional_rangos.xml",
        "views/wizard_plan_vacacional.xml",
        "views/wizard_percepcion.xml",
        "views/wizard_empleado.xml",
        "views/wizard_nomina.xml",
        "views/wizard_dias.xml",
        "views/wizard_app.xml",
        "views/aguinaldo_plan.xml",
        "views/aguinaldo_rangos.xml",
        "views/cronjob_vacaciones.xml",
        "views/aguinaldo_categoria.xml",
        "views/vacaciones_historial.xml",
        "views/prima_vacacional_factor.xml",
        "views/factor_riesgo_trabajo.xml",
        "views/vacacional_categoria.xml",
        "views/derecho_vacacional.xml",
        "views/vacacional_rangos.xml",
        "views/nomina_percepcion.xml",
        "views/nomina_concepto.xml",
        "views/plan_vacacional.xml",
        "views/dia_hora_linea.xml",
        "views/employee_ext.xml",
        "views/periodo_pago.xml",
        "views/vacaciones.xml",
        "views/jornada.xml",
        "views/nomina.xml",
        "views/uma.xml",
        "views/01-menu.xml",
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
