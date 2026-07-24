# -*- coding: utf-8 -*-
{
    "name": "Portal Web Empleados",  # pyright: ignore
    "summary": "Portal web de administracion única por empleado.",
    "description": """
        Permite el manejo de contraseñas (login).
        Permite a cada usuario un portal web para ingreso
        de datos, documentos, y pase de asistencias.
        """,
    "author": "Andrés Alberto López Mendoza / Nentria",
    "website": "https://github.com/AeroGenCreator",
    "category": "web",
    "version": "0.1",
    "depends": ["hr", "portal", "doc", "geo"],
    "data": ["views/templates.xml", "views/employee_ext.xml"],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "assets": {
        "web.assets_frontend": [
            "net/static/src/js/net_checkin.js",
            "net/static/css/style.css",
        ],
    },
}
