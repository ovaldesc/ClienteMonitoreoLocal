# core/sistema_operativo.py

import platform
from importlib import import_module


def detectar_so():
    system = platform.system()
    if system == "Windows":
        return {
            "sistema": "windows.sistema",
            "usuarios": "windows.usuarios",
            "seguridad": "windows.seguridad",
            "dispositivos": "windows.dispositivos",
            "red": "windows.red",
            "antivirus": "windows.antivirus_info",
        }
    elif system == "Linux":
        return {
            "sistema": "linux.sistema",
            "usuarios": "linux.usuarios",
            "seguridad": "linux.seguridad",
            "dispositivos": "linux.dispositivos",
            "red": "linux.red",
            "antivirus": "linux.antivirus_info",
        }
    else:
        raise OSError("Sistema operativo no soportado")


def cargar_modulo(modulo_path):
    return import_module("sistema.{}".format(modulo_path))
