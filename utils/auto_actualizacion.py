# utils/auto_actualizacion.py

import os
import sys
import shutil
import hashlib
from .config_manager import ConfigManager
from .scheduler import registrar_tarea_programada

def _hash_archivo(ruta):
    """Calcula el hash SHA256 de un archivo."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(ruta, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return None

def _get_ruta_instalada():
    """Devuelve la ruta de la copia instalada en la carpeta de configuración."""
    config = ConfigManager()
    if getattr(sys, 'frozen', False):
        exe_name = "ClienteMonitoreo.exe" if sys.platform == "win32" else "ClienteMonitoreo.exe"
        return os.path.join(config.config_dir, exe_name)
    else:
        return os.path.join(config.config_dir, "main.py")

def auto_actualizar_si_necesario():
    """
    Compara el ejecutable actual con la copia instalada.
    Si el actual es más nuevo, lo copia y re-registra la tarea.
    Solo se ejecuta si está empaquetado con PyInstaller.
    """
    if not getattr(sys, 'frozen', False):
        return  # Solo en modo .exe

    ruta_actual = sys.executable
    ruta_instalada = _get_ruta_instalada()

    # Si no existe la copia instalada, no hay nada que actualizar
    if not os.path.exists(ruta_instalada):
        return

    hash_actual = _hash_archivo(ruta_actual)
    hash_instalada = _hash_archivo(ruta_instalada)

    if hash_actual and hash_instalada and hash_actual != hash_instalada:
        print("Nueva versión detectada. Actualizando copia instalada...")
        try:
            # Copiar el ejecutable actual sobre la copia instalada
            shutil.copy2(ruta_actual, ruta_instalada)
            # Re-registrar la tarea programada
            registrar_tarea_programada()
            print("Actualización completada.")
        except Exception as e:
            print("Error al actualizar: {}".format(str(e)))