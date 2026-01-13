# services/recoleccion.py

from core.sistema_operativo import detectar_so, cargar_modulo
from services.escaneo import escanear_puertos
from utils.utiles import EjecutorParalelo
import datetime
import platform

# --- Constantes y mapeos (mover desde main.py) ---
MODULOS_KEYS = {
    "sistema": "sistema",
    "usuarios": "usuarios",
    "seguridad": "seguridad",
    "dispositivos": "dispositivos",
    "red": "red",
    "antivirus": "antivirus",
}

CLASES_POR_SO = {
    "sistema": {"windows": "SistemaWindows", "linux": "SistemaLinux"},
    "usuarios": {"windows": "UsuarioWindows", "linux": "UsuarioLinux"},
    "seguridad": {"windows": "SeguridadWindows", "linux": "SeguridadLinux"},
    "dispositivos": {"windows": "DispositivoWindows", "linux": "DispositivoLinux"},
    "red": {"windows": "RedWindows", "linux": "RedLinux"},
    "antivirus": {"windows": "AntivirusInfoWindows", "linux": "AntivirusInfoLinux"},
}

def obtener_tipo_so(so_string):
    return "windows" if "windows" in so_string.lower() else "linux"

def crear_instancia_modulo(modulo, tipo_so, nombre_modulo):
    try:
        nombre_clase = CLASES_POR_SO[nombre_modulo][tipo_so]
        if not hasattr(modulo, nombre_clase):
            raise AttributeError("Clase {} no encontrada en módulo {}".format(nombre_clase,nombre_modulo))
        return getattr(modulo, nombre_clase)()
    except Exception:
        return None

def inicializar_modulos(so_data):
    modulos = {}
    for nombre, key in MODULOS_KEYS.items():
        try:
            modulos[nombre] = cargar_modulo(so_data[key])
        except Exception:
            return {}
    instancias = {}
    for nombre, modulo in modulos.items():
        if modulo is not None:
            tipo_so = obtener_tipo_so(so_data[nombre])
            instancia = crear_instancia_modulo(modulo, tipo_so, nombre)
            if instancia is not None:
                instancias[nombre] = instancia
    return instancias

def configurar_tareas_recoleccion(ejecutor, instancias, ip):
    tareas = [
        ("nombre_pc", instancias["sistema"].obtener_nombre_pc),
        ("version_so", instancias["sistema"].get_version_so),
        ("fecha", lambda: datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")),
        ("usuario_activo", instancias["usuarios"].get_usuario_activo),
        ("aplicaciones", instancias["sistema"].get_installed_apps),
        ("usuarios", instancias["usuarios"].get_usuarios),
        ("admins", instancias["usuarios"].get_admins),
        ("parches", instancias["seguridad"].get_parches_seguridad),
        ("escritorio_remoto", instancias["seguridad"].is_escritorio_remoto_habilitado),
        ("dispositivos", instancias["dispositivos"].get_dispositivos_conectados),
        ("historial", instancias["dispositivos"].get_historial_dispositivos),
        ("estado_usb", instancias["dispositivos"].get_estado_usb),
        ("carpetas", instancias["red"].get_carpetas_compartidas),
        ("kms", instancias["seguridad"].esta_unido_kms),
        ("segurmatica", instancias["antivirus"].get_segurmatica_info),
        ("puertos", escanear_puertos, (ip or "127.0.0.1",)),
    ]
    if platform.system().lower() == "windows":
        tareas.append(("info_kaspersky", instancias["antivirus"].get_kaspersky_info))
    else:
        ejecutor.agregar_tarea(
            "info_kaspersky",
            lambda: {"mensaje": "El antivirus kaspersky no se encuentra disponible en Linux"}
        )
    for tarea in tareas:
        if len(tarea) == 3:
            ejecutor.agregar_tarea(tarea[0], tarea[1], args=tarea[2])
        else:
            ejecutor.agregar_tarea(tarea[0], tarea[1])

def estructurar_datos_finales(resultados, ip):
    segurmatica_raw = resultados.get("segurmatica", {})
    segurmatica_final = segurmatica_raw["mensaje"] if isinstance(segurmatica_raw, dict) and "mensaje" in segurmatica_raw else segurmatica_raw

    kaspersky_raw = resultados.get("info_kaspersky", {})
    if isinstance(kaspersky_raw, dict):
        if "mensaje" in kaspersky_raw:
            kaspersky_final = kaspersky_raw["mensaje"]
        elif "error" in kaspersky_raw:
            kaspersky_final = kaspersky_raw["error"]
        else:
            kaspersky_final = kaspersky_raw
    else:
        kaspersky_final = kaspersky_raw

    return {
        "Nombre PC": resultados.get("nombre_pc", "Desconocido"),
        "Version SO": resultados.get("version_so", "Desconocido"),
        "IP": ip,
        "Fecha Ejecución": resultados.get("fecha", "Desconocido"),
        "Usuario Activo": resultados.get("usuario_activo", "Desconocido"),
        "Aplicaciones Instaladas": resultados.get("aplicaciones", []),
        "Usuarios": resultados.get("usuarios", []),
        "Administradores": resultados.get("admins", []),
        "Parches de Seguridad": resultados.get("parches", []),
        "Escritorio Remoto": resultados.get("escritorio_remoto", "Desconocido"),
        "Dispositivos Conectados": resultados.get("dispositivos", {}),
        "Historial Dispositivos": resultados.get("historial", []),
        "Puertos USB": resultados.get("estado_usb", "Desconocido"),
        "Puertos Abiertos": resultados.get("puertos", []),
        "Carpetas Compartidas": resultados.get("carpetas", []),
        "Unido a KMS": resultados.get("kms", False),
        "Información de Segurmática": segurmatica_final,
        "Información de Kaspersky": kaspersky_final,
    }

def recolectar_datos_completos():
    """Ejecuta todo el flujo de recolección y devuelve (datos, instancias, ip_local)"""
    so_data = detectar_so()
    instancias = inicializar_modulos(so_data)
    if not instancias:
        raise Exception("No se pudieron inicializar los módulos del sistema")
    ip_local = instancias["sistema"].get_ip()
    ejecutor = EjecutorParalelo()
    configurar_tareas_recoleccion(ejecutor, instancias, ip_local)
    resultados = ejecutor.ejecutar()
    datos = estructurar_datos_finales(resultados, ip_local)
    return datos, instancias, ip_local