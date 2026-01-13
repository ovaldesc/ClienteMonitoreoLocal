#utils/consola.py
import sys

def ocultar_consola_si_no_interactiva():
    """
    En Windows, oculta la ventana de consola si:
    - Ya existe configuración válida
    - No se pasó --reconfigurar
    Solo aplica si se compiló SIN --windowed (es decir, con consola).
    """
    if sys.platform != "win32":
        return

    from utils.config_manager import ConfigManager
    config_mgr = ConfigManager()
    conf_existe = config_mgr.cargar_configuracion() is not None
    reconfigurar = "--reconfigurar" in sys.argv

    if conf_existe and not reconfigurar:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                user32.ShowWindow(hwnd, 0)  # SW_HIDE
        except Exception:
            pass  # Si falla, no pasa nada; seguimos en modo consola