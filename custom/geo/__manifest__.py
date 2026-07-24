# -*- coding: utf-8 -*-
{
    "name": "Administra Geolocalización",  # pyright: ignore
    "summary": "Configuración de la geolocalización para el pase de lista.",
    "description": """
    Construye modelos para administrar planes de geolocalización para
    empleados activos. Permite la union de componentes JS con Python Odoo
    para la obtencion de coordenadas.
    """,
    "author": "Andrés Alberto López Mendoza / Nentria",
    "website": "https://github.com/AeroGenCreator",
    "category": "hr",
    "version": "0.1",
    "depends": ["hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/ubicacion.xml",
        "views/employee_ext.xml",
        "views/categoria.xml",
        "views/plan.xml",
        "views/menus.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "assets": {
        "web.assets_backend": [
            "geo/static/src/js/geo_widget.js",
            "geo/static/src/js/geo_widget.xml",
        ],
    },
}
