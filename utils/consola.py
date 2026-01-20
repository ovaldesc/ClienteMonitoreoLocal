# utils/consola.py

import sys
import os
import ctypes
from utils.config_manager import ConfigManager
def es_admin():
    """Devuelve True si se está ejecutando con privilegios de administrador (Windows) o root (Linux)."""
    if sys.platform == "win32":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

def ocultar_consola_si_no_interactiva():
    """
    En Windows, oculta la ventana de consola si:
    - Ya existe configuración válida
    - No se pasó --reconfigurar
    Solo aplica si se compiló SIN --windowed.
    """
    if sys.platform != "win32":
        return
    config_mgr = ConfigManager()
    conf_existe = config_mgr.cargar_configuracion() is not None
    reconfigurar = "--reconfigurar" in sys.argv
    if conf_existe and not reconfigurar:
        try:
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                user32.ShowWindow(hwnd, 0)  # SW_HIDE
        except Exception:
            pass