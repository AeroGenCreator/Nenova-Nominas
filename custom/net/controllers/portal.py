# Compañia: Nentria
# Desarrollador: Andres Alberto Lopez Mendoza
# Version 1.0.0
# Portal WEB - Empleados

# Modulos Python
import base64
import datetime
from dataclasses import dataclass

# Establecer zona horaria México
import pytz  # pyright: ignore

# Herramientas odoo para generación de sitios web
from odoo import fields, http  # pyright: ignore
from odoo.http import request  # pyright: ignore

# ZONA HORARIA MEXICO.
TZ_MEXICO = pytz.timezone("America/Mexico_City")

# Parsea los meses a un string valido para queries.
MONTH_PARSER = {
    1: "01",
    2: "02",
    3: "03",
    4: "04",
    5: "05",
    6: "06",
    7: "07",
    8: "08",
    9: "09",
    10: "10",
    11: "11",
    12: "12",
}


# CONTENEDOR DE DATOS: CONTEXTO FECHAS
@dataclass(frozen=True)
class ContextoFechas:
    now: datetime.datetime
    now_utc: datetime.datetime
    mex_datetime: datetime.datetime
    mex_today: datetime.date
    mex_current_year: int
    mex_current_month: int
    mex_next_month: int
    mex_variable_year: int


def contexto_fechas():
    NOW = datetime.datetime.now()
    NOW_UTC = NOW.replace(tzinfo=pytz.utc)
    MEX_DATETIME = NOW_UTC.astimezone(TZ_MEXICO)
    MEX_TODAY = MEX_DATETIME.date()
    MEX_CURRENT_YEAR = MEX_DATETIME.year
    MEX_CURRENT_MONTH = MEX_DATETIME.month
    MEX_NEXT_MONTH = MEX_DATETIME.month + 1 if MEX_DATETIME.month < 12 else 1
    if MEX_CURRENT_MONTH == 12 and MEX_NEXT_MONTH == 1:
        MEX_VARIABLE_YEAR = MEX_CURRENT_YEAR + 1
    else:
        MEX_VARIABLE_YEAR = MEX_CURRENT_YEAR
    kwargs = {
        "now": NOW,
        "now_utc": NOW_UTC,
        "mex_datetime": MEX_DATETIME,
        "mex_today": MEX_TODAY,
        "mex_current_year": MEX_CURRENT_YEAR,
        "mex_current_month": MEX_CURRENT_MONTH,
        "mex_next_month": MEX_NEXT_MONTH,
        "mex_variable_year": MEX_VARIABLE_YEAR,
    }
    return ContextoFechas(**kwargs)


# Mensaje global, se perdio estado de sesion:
GLOBAL_MSG = (
    "Se perdio el estado de sesión. "
    "validar sus credenciales nuevamente "
    "para ingresar al portal web."
)


# Función borrar mensaje global fuera de login.
def borrar_global_msg(request, key):
    msg = request.session.get(key, False)
    if msg:
        del request.session[key]


# Clase Padre; "NetPortal"
class NetPortal(http.Controller):
    # === REDIRECCION PORTAL WEB ===
    @http.route(["/login"], type="http", auth="public", website=True, methods=["GET"])
    def login(self, **kw):
        # Cache: limpiar id | email | password | error_de_ip
        employee_id = request.session.get("employee_id", None)
        email = request.session.get("email", None)
        password = request.session.get("password", None)
        ubicacion_error = request.session.get("ubicacion_error", None)
        company = request.session.get("company", None)
        global_msg = request.session.get("global_msg", False)

        if employee_id is not None:
            del request.session["employee_id"]
        if email is not None:
            del request.session["email"]
        if password is not None:
            del request.session["password"]
        if company is not None:
            del request.session["company"]
        if ubicacion_error is not None:
            del request.session["ubicacion_error"]

        if global_msg:
            kw.update({"global_msg": global_msg})

        # Query a la primera empresa de la lista.
        domain = []
        company = request.env["res.company"].search(domain, limit=1)
        LOGO = False
        mimetype = "image/png"
        if company:
            LOGO = company.logo_web.decode("utf-8")
            if LOGO.startswith(("PD94bWw", "PHN2Z")):
                mimetype = "image/svg+xml"
            elif LOGO.startswith("/9j/"):
                mimetype = "image/jpeg"
            elif LOGO.startswith("R0lGOD"):
                mimetype = "image/gif"

        kw.update({"logo_web": LOGO})
        kw.update({"mimetype": mimetype})

        # Renderiza: Login Portal
        return request.render("net.login_screen", kw)

    # === VALIDACION DE CREDENCIALES ===
    @http.route(
        ["/validar"],
        type="http",
        auth="public",
        website=True,
        methods=["POST", "GET"],
        csrf=False,
    )
    def nentria(self, **kw):
        """
        Logica de validacion y contruccion de metadata
        previo al renderizado de la plantilla net.my_space
        """

        # Borrar mensaje global, si existe:
        borrar_global_msg(request=request, key="global_msg")

        # Obtencion de errores y mensajes.
        error = request.session.get("error_carga_documento", None)
        attendance_id = request.session.get("attendance_id", None)

        # Limpiar el cache:
        if error is not None:
            del request.session["error_carga_documento"]
        if attendance_id is not None:
            del request.session["attendance_id"]

        # Borrar Cache Assitencias | Se recalculan mas abajo
        CHECK_IN = request.session.get("puede_entrar", None)
        CHECK_OUT = request.session.get("puede_salir", None)
        COMPLETED = request.session.get("dia_completado", None)
        if CHECK_IN:
            del request.session["puede_entrar"]
        if CHECK_OUT:
            del request.session["puede_salir"]
        if COMPLETED:
            del request.session["dia_completado"]

        # Credenciales recibidas desde el login.
        email = kw.get("email", None)
        password = kw.get("password", None)

        # Si no existen las credenciales en el formulario login.
        # Se obtiene de la sesion actual. (Esto ayuda a la redirección)
        if email is None and password is None:
            email = request.session.get("email", None)
            password = request.session.get("password", None)

        msg = (
            "Error en las credenciales. Revisar datos "
            "y que el usuario este dado de alta en en la empresa."
        )

        # Si las credenciales no existen.
        if email is None and password is None:
            kw.update({"error": msg})
            return request.render("net.login_screen", kw)

        # Se guardan las credenciales en la sesión.
        request.session["email"] = email
        request.session["password"] = password

        # Si hay credenciales; query al recordset del empleado.
        domain = [
            ("work_email", "=", email),
            ("contraseña_portal", "=", password),
        ]
        employee = request.env["hr.employee"].sudo().search(domain, limit=1)
        # Si no se validan las credenciales con la BD, regresa al login: error.
        if not employee:
            kw.update({"error": msg})
            return request.render("net.login_screen", kw)

        # Obtencion del id del empleado.
        employee_id = employee.id
        # Se guarda el id y el recordset del usuario en "session"
        request.session["employee_id"] = employee_id

        # Query a la empresa del empleado && se guarda en la sesión:
        company_recordset = employee.company_id.filtered(
            lambda r: r.id == employee.company_id.id
        )
        COMPANY = company_recordset.name
        request.session["company"] = COMPANY

        # Rango de fechas (Limita al mes actual)
        fechas = contexto_fechas()
        range = [
            f"{fechas.mex_current_year}-{MONTH_PARSER[fechas.mex_current_month]}-01",
            f"{fechas.mex_variable_year}-{MONTH_PARSER[fechas.mex_next_month]}-01",
        ]

        # Query; Obtener suma de horas trabajadas de este mes.
        hours_domain = [
            ("employee_id", "=", employee_id),
            ("date", ">=", range[0]),
            ("date", "<", range[1]),
        ]
        hours = (
            request.env["hr.attendance"]
            .sudo()
            ._read_group(hours_domain, aggregates=["worked_hours:sum"])
        )
        this_month_hours = round(hours[0][0], 2) if hours[0][0] else 0.0
        # Evaluar asistencia de este dia; empleado actual
        day_domain = [
            ("date", "=", fechas.mex_datetime.replace(tzinfo=None).isoformat())
        ]
        this_day_attendances = request.env["hr.attendance"].sudo().search(day_domain)

        check_in = this_day_attendances.filtered_domain(
            [("check_in", "!=", False), ("employee_id", "=", employee_id)]
        )
        check_out = this_day_attendances.filtered_domain(
            [("check_out", "!=", False), ("employee_id", "=", employee_id)]
        )

        # Variables de conversión (Odoo) -> (Mexico)
        fecha_hora_entrada = False
        fecha_hora_salida = False
        time_code = "%Y-%m-%-d %H:%M"

        # Horas Mexico: Si existen registros. (Desde Odoo a Mexico)
        if check_in.check_in:
            # Hora entrada (Mexico) (Isoformat)
            fecha_hora_entrada = check_in.check_in
            if fecha_hora_entrada.tzinfo is None:
                fecha_hora_entrada = fecha_hora_entrada.replace(tzinfo=pytz.utc)
            fecha_hora_entrada = fecha_hora_entrada.astimezone(TZ_MEXICO)
            fecha_hora_entrada = fecha_hora_entrada.strftime(time_code)
        if check_out.check_out:
            # Hora salida (Mexico) (Isoformat)
            fecha_hora_salida = check_out.check_out
            if fecha_hora_salida.tzinfo is None:
                fecha_hora_salida = fecha_hora_salida.replace(tzinfo=pytz.utc)
            fecha_hora_salida = fecha_hora_salida.astimezone(TZ_MEXICO)
            fecha_hora_salida = fecha_hora_salida.strftime(time_code)

        # Si no existe entrada, puede crear una.
        if not check_in and not check_out:
            request.session["puede_entrar"] = True
        # Si existe entrada y salida. Bloquear boton.
        elif check_in and check_out:
            kw.update({"hora_entrada": fecha_hora_entrada})
            kw.update({"hora_salida": fecha_hora_salida})
            request.session["dia_completado"] = True
        # Si ya registro una entrada; Puede registrar salida
        elif check_in:
            kw.update({"hora_entrada": fecha_hora_entrada})
            request.session["attendance_id"] = check_in.id
            request.session["puede_salir"] = True

        # Extraer: Banderas de estado para renderizado "Boton Asistencias"
        entrada = request.session.get("puede_entrar", None)
        salida = request.session.get("puede_salir", None)
        dia_completo = request.session.get("dia_completado", None)
        ubicacion_error = request.session.get("ubicacion_error", None)
        check_out_validation = request.session.get("check_out_validation", None)

        # Se guardan los datos para el frontend.
        kw.update({"employee_name": employee.name})
        kw.update({"this_month_hours": this_month_hours})
        kw.update({"puede_entrar": entrada or False})
        kw.update({"puede_salir": salida or False})
        kw.update({"dia_completado": dia_completo or False})
        kw.update({"ubicacion_error": ubicacion_error or False})
        kw.update({"check_out_validation": check_out_validation})
        kw.update({"company": COMPANY})

        # Se renderiza (my_space)
        return request.render("net.my_space", kw)

    # === VOLVER A HOME ===
    @http.route(
        ["/net/home"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def home(self, **kw):
        # Valida que existe un empleado.
        employee_id = request.session.get("employee_id", False)

        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        if not employee_id:
            request.session["global_msg"] = GLOBAL_MSG
            return request.redirect("/login")

        # Guarda credenciales de login.
        employee = request.env["hr.employee"].sudo().browse(employee_id)
        request.session["email"] = employee.work_email
        request.session["password"] = employee.contraseña_portal

        # Redirige a la validacion -> Luego "Home".
        return request.redirect("/validar")

    # === REGISTRAR ENTRADA ===
    @http.route(
        ["/check_in"],
        type="json2",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=False,
    )
    def check_in(self, **kw):
        """
        Componente JS captura el evento del boton.
        Obtiene la ubicación y esta a su vez es validada con el empleado
        y sus ubicaciones permitidas para pase de lista.
        """

        # Cache: Limpiar ubicacion_error.
        ubicacion_error = request.session.get("ubicacion_error", None)
        if ubicacion_error is not None:
            del request.session["ubicacion_error"]

        # Validar que hay un usuario en la sesion.
        employee_id = request.session.get("employee_id", None)

        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        if employee_id is None:
            request.session["global_msg"] = GLOBAL_MSG
            request.redirect("/login")

        # === Validación por area permitida ===
        # 1. Query a los planes -> ubicaciones - del empleado
        domain = [("id", "=", employee_id)]
        singleton = request.env["hr.employee"].sudo().search(domain)
        employee_plans = singleton.plan_ids.filtered(
            lambda r: r.empleado_id.id == employee_id
        )

        # 2. Extraccion de los datos en una lista blanca de ubicaciones
        ubicaciones = []
        for rec in employee_plans:
            for linea in rec.plan_id.plan_ubicacion_ids:
                ubicaciones.append(linea.ubicacion_id.area)

        # 3. Validamos la ubicación de la peticion con la lista blanca.
        params = kw.get("params", "")
        ERROR_MSG = (
            "Su ubicación no ha sido validada. "
            "Dos posibles escensarios: Su ubicación no esta dada de alta "
            "en la empresa o su dispositivo no dio respuesta GPS de ubicación."
        )

        # 4. Extracción y validacion de ubicación - JSON devuelto por el JS.
        if not params:
            request.session["ubicacion_error"] = ERROR_MSG
            return request.redirect("/validar")
        area = params.get("area", "")
        if area not in ubicaciones:
            request.session["ubicacion_error"] = ERROR_MSG
            return request.redirect("/validar")

        # Se registra el pase de lista:
        dicc = {
            "employee_id": employee_id,
            "date": fields.Date.today(),
            "check_in": fields.Datetime.now(),
        }

        request.env["hr.attendance"].sudo().create(dicc)
        return request.redirect("/validar")

    # === REGISTRAR SALIDA ===
    @http.route(
        ["/check_out"],
        type="http",
        auth="public",
        website=True,
        methods=["POST", "PUT"],
        csrf=False,
    )
    def check_out(self, **kw):
        # Limpiar; Cache error de limite.
        validation = request.session.get("check_out_validation", None)
        if validation:
            del request.session["check_out_validation"]

        # Obtencion (id del empleado)
        employee_id = request.session.get("employee_id", None)

        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        if employee_id is None:
            request.session["global_msg"] = GLOBAL_MSG
            return request.redirect("/login")

        # ID de la asitencia actual (CHECK IN)
        attendance_id = request.session.get("attendance_id", None)
        if attendance_id is None:
            return request.redirect("/validar")

        # Obtención del Recordset
        recordset = request.env["hr.attendance"].sudo().browse(attendance_id)

        # Prevencion de retraso entre entrada y salida.
        ENTRADA = recordset.check_in
        LIMITE = ENTRADA + datetime.timedelta(minutes=10)
        AHORA = fields.Datetime.now()

        if AHORA < LIMITE:
            msg = (
                "Para poder registrar una salida se requiere un lapso "
                "de 10 minutos como minimo."
            )
            request.session["check_out_validation"] = msg
            return request.redirect("/validar")

        # Diccionario de valores para hr.attendance
        recordset.sudo().write({"check_out": fields.Datetime.now()})

        # Refrescar widgets
        return request.redirect("/validar")

    # === EMPLEDO INFORMACION PERSONAL ===
    @http.route(
        ["/my_data"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def my_data(self, **kw):

        # Si no hay id o compañia. Volver al login
        employee_id = request.session.get("employee_id", False)
        COMPANY = request.session.get("company", False)

        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        validate = ((employee_id), (COMPANY))
        if not all(validate):
            request.session["global_msg"] = GLOBAL_MSG
            return request.redirect("/login")

        # Extraccion Recordset del Empleado.
        employee = request.env["hr.employee"].sudo().browse(employee_id)

        # Extraccion Recordset del Contrato del Empleado.
        contract_domain = [
            ("empleado_id", "=", employee_id),
            ("active", "=", True),
        ]
        contract = request.env["contrato"].sudo().search(contract_domain, limit=1)

        # A traves de filtered() -> Extracción de "Documentos Empleado"
        documents = employee.documento_ids.filtered(
            lambda r: r.active and r.empleado_id.id == employee_id
        )
        documentos_lista = [
            {
                "id": doc.id,
                "nombre": doc.name,
                "tipo": doc.documento_tipo_id.name,
            }
            for doc in documents
        ]

        # Diccionario para el renderizado en UI.
        kw["name"] = employee.name
        kw["work_email"] = employee.work_email
        kw["mobile_phone"] = employee.mobile_phone
        kw["contraseña_portal"] = employee.contraseña_portal
        kw["expiration_date"] = contract.vigencia
        kw["contract_id"] = contract.id
        kw["active_documents"] = documentos_lista
        kw["company"] = COMPANY

        # Ruta del template.
        return request.render("net.my_data", kw)

    # === EDITAR FORMULARIO DE INFORMACION EMPLEADO ===
    @http.route(
        ["/editar-formulario"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def edit_form(self, **kw):

        # Validar "id" y "compañia" de empleado en sesión.
        employee_id = request.session.get("employee_id", False)
        COMPANY = request.session.get("company", False)
        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        validate = ((employee_id), (COMPANY))
        if not all(validate):
            request.session["global_msg"] = GLOBAL_MSG
            return request.redirect("/login")

        # Extracción:
        # request.session["global_msg"] = GLOBAL_MSG Datos del empleado (Editables).
        employee = request.env["hr.employee"].sudo().browse(employee_id)
        kw["employee_id"] = employee_id
        kw["name"] = employee.name
        kw["work_email"] = employee.work_email
        kw["mobile_phone"] = employee.mobile_phone
        kw["contraseña_portal"] = employee.contraseña_portal
        kw["company"] = COMPANY

        # Renderiza formulario de edción.
        return request.render("net.editar_formulario", kw)

    # === LOGICA POST | PUT "GUARDA CAMBIOS DE FORMULARIO INFO EMPLEADO" ===
    @http.route(
        ["/nentria/guardar-edicion"],
        type="http",
        auth="public",
        website=True,
        methods=["POST", "PUT"],
        csrf=False,
    )
    def guardar_cambios(self, **kw):

        # Validar "id" de empleado en sesión.
        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        employee_id = request.session.get("employee_id", False)
        if not employee_id:
            request.session["global_msg"] = GLOBAL_MSG
            return request.redirect("/login")

        # Extracción de datos desde el formulario de edición.
        name = kw.get("name", "")
        work_email = kw.get("work_email", "")
        mobile_phone = kw.get("mobile_phone", "")
        contraseña_portal = kw.get("contraseña_portal", "")

        # Actualizacion en la base de datos.
        EMPLOYEE = request.env["hr.employee"].sudo().browse(employee_id)
        EMPLOYEE.sudo().write(
            {
                "name": name,
                "work_email": work_email,
                "mobile_phone": mobile_phone,
                "contraseña_portal": contraseña_portal,
            }
        )

        # Renderiza vista; informacion del usuario.
        return request.redirect("/my_data")

    # === PREPARA Y RENDERIZA EL FORMULARIO DE DOCUMENTOS ===
    @http.route(
        ["/carga-documentos"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def subir_documentos(self, **kw):

        # Validar el "id" y "compañia".
        employee_id = request.session.get("employee_id", False)
        COMPANY = request.session.get("company", False)

        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        validate = ((employee_id), (COMPANY))
        if not all(validate):
            request.session["global_msg"] = GLOBAL_MSG
            return request.redirect("/login")

        # Si hay mensaje de error proceso anterior:
        # request.session["global_msg"] = GLOBAL_MSG Asignarlo para UI.
        error = request.session.get("error_carga_documento", None)
        if error is not None:
            kw.update({"error_carga_documento": error})

        # Se manda el "id" al UI.
        kw.update({"employee_id": employee_id})

        # Recordsets de "tipos de datos" que ("Esten marcados como activos").
        domain_tipos = [("active", "=", True)]

        # Recordset del empleado.
        recordsets = request.env["documento.tipo"].sudo().search(domain_tipos)
        empleado = request.env["hr.employee"].sudo().browse(employee_id)

        # Filtered -> Documentos del empleado.
        active_documents = empleado.documento_ids.filtered(
            lambda r: r.empleado_id.id == employee_id and r.active
        )

        # Lista de "tipos de documentos" en documentos activos del empleado.
        if active_documents:
            empleado_docs = [rec.documento_tipo_id.name for rec in active_documents]
        else:
            empleado_docs = {}

        # Lista de "tipos de documentos" completa.
        if recordsets:
            complete = [rec.name for rec in recordsets]
        else:
            complete = {}

        # OPERACIÓN: Elementos en "completos" que NO estan en "empleado_docs".
        OPTIONS_EMPLEADO = list(set(complete) - set(empleado_docs))

        # Unicamente se mostraran documentos faltantes por empleado en la UI.
        kw.update({"options": OPTIONS_EMPLEADO})
        kw.update({"company": COMPANY})

        # Renderizado de la vista "carga de documentos".
        return request.render("net.carga_documentos", kw)

    # === Guardar nuevo documento PDF ===
    @http.route(
        ["/guardar-documento"],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=False,
    )
    def guardar_documento(self, **kw):

        # Cache: Si existe el error limpiarlo.
        error = request.session.get("error_carga_documento", None)
        if error:
            del request.session["error_carga_documento"]

        # Validar "id".
        empleado_id = request.session.get("employee_id", None)

        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        if not empleado_id:
            request.session["global_msg"] = GLOBAL_MSG
            return request.redirect("/login")

        # Extraccion de datos desde el formulario.
        tipo = kw.get("tipo_documento", None)
        nombre = kw.get("nombre", None)
        PDF_FILE = kw.get("pdf", None)

        # Si faltan campos: crear error
        validate = ((not nombre), (not PDF_FILE), (not tipo))
        if any(validate):
            request.session["error_carga_documento"] = (
                "Todos los campos del formulario son obligatorios."
            )
            # Redirige a la vista: "carga-documentos"
            return request.redirect("/carga-documentos")

        # Setear cursor de lectura | Parseo de FileStorage a Base64
        if PDF_FILE is not None:
            PDF_FILE.seek(0)
            BASE_SIX_FOUR = base64.b64encode(PDF_FILE.read()).decode("utf-8")
        else:
            request.session["error_carga_documento"] = (
                f"Error al intentar parsing de PDF. Se obtuvo {type(PDF_FILE)}"
            )
            # Redirige a la vista: "carga-documentos"
            return request.redirect("/carga-documentos")

        # Obtencion del "id" del tipo de documento
        domain = [("name", "=", tipo)]
        tipo_id = request.env["documento.tipo"].sudo().search(domain, limit=1).ids[0]

        dicc = {
            "name": nombre,
            "empleado_id": empleado_id,
            "fecha": fields.Date.today(),
            "documento_tipo_id": tipo_id,
            "active": True,
            "documento_pdf": BASE_SIX_FOUR,
        }

        # Se guardan los datos en la BD.
        try:
            request.env["documento"].sudo().create(dicc)
            return request.redirect("/my_data")
        except Exception as e:
            request.session["error_carga_documento"] = e
            return request.render("/carga-documento")

    # === PREPARA Y RENDERIZA VISTA DE CONTRATO ===
    @http.route(
        ["/my-contract"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def ver_contrato(self, **kw):
        # Validar "id" del usuario.
        employee_id = request.session.get("employee_id", False)
        COMPANY = request.session.get("company", False)

        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        validate = ((employee_id), (COMPANY))
        if not all(validate):
            request.session["global_msg"] = GLOBAL_MSG
            request.redirect("/login")

        # Se busca el contrato activo del empleado. Limitado a 1.
        domain = [("empleado_id", "=", employee_id), ("active", "=", True)]
        contrato_activo = request.env["contrato"].sudo().search(domain, limit=1)

        # Preparación de datos para la UI.
        kw.update({"nombre": contrato_activo.name})
        kw.update({"pdf": contrato_activo.contrato_pdf})
        kw.update({"company": COMPANY})

        # Renderizado: vista de PDF's
        return request.render("net.ver_pdfs", kw)

    # === PREPARA Y RENDERIZA VISTA DOCUMENTO ===
    # La ruta contiene una variable embedida "<int: doc_id>"
    @http.route(
        ["/ver-documento/<int:doc_id>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def ver_documento(self, doc_id, **kw):
        # Validar que haya nombre de empresa
        COMPANY = request.session.get("company", False)

        # Borrar mensaje de error antes de validar perdida de credenciales
        borrar_global_msg(request=request, key="global_msg")

        if not COMPANY:
            request.session["global_msg"] = GLOBAL_MSG
            return request.redirect("/login")

        # Se variable como argumento a la función del controlador
        # Se busca el documento por "id" en la base de datos.
        documento = request.env["documento"].sudo().browse(doc_id)

        # Si no hay recordset, redirigi a error.
        if not documento:
            return request.render("website.404")

        # Si existe el documento, pasamos la informacion al frontend PDF.
        kw.update({"nombre": documento.name})
        kw.update({"pdf": documento.documento_pdf})
        kw.update({"company": COMPANY})

        # Renderizado: vista de PDF's
        return request.render("net.ver_pdfs", kw)
