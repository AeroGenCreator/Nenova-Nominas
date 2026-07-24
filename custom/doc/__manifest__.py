# -*- coding: utf-8 -*-
{
    "name": "Documentos Empleados",  # pyright: ignore
    "summary": "Carga documentos para cada empledado.",
    "description": """
    Extiende modulo hr.employee para admitir la carga y
    organización de documentos.
    """,
    "author": "Andrés Alberto López Mendoza / Nentria",
    "website": "https://github.com/AeroGenCreator",
    "category": "hr",
    "version": "0.1",
    "depends": ["hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/documento_tipo.xml",
        "views/employee_ext.xml",
        "views/contrato.xml",
        "views/documento.xml",
        "views/menu.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
}
