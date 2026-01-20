# utils/scheduler.py

import os
import sys
import shutil
import subprocess
import platform
from .config_manager import ConfigManager
import ctypes
from ctypes import wintypes
from .consola import es_admin

def _get_ruta_instalada():
    """Ruta global del binario instalado."""
    system = platform.system().lower()
    if system == "windows":
        if platform.machine().endswith('64'):
            base = r"C:\Program Files (x86)"
        else:
            base = r"C:\Program Files"
        return os.path.join(base, "ClienteMonitoreoLocal", "ClienteMonitoreo.exe")
    elif system == "linux":
        return "/opt/ClienteMonitoreoLocal/ClienteMonitoreo"
    else:
        raise OSError("Sistema no soportado")

def _copiar_ejecutable_a_config():
    destino = _get_ruta_instalada()
    if os.path.exists(destino):
        return destino
    if getattr(sys, 'frozen', False):
        origen = sys.executable
    else:
        origen = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    try:
        dir_destino = os.path.dirname(destino)
        if not os.path.exists(dir_destino):
            os.makedirs(dir_destino)
        shutil.copy2(origen, destino)
        if platform.system() != "Windows":
            os.chmod(destino, 0o755)
        return destino
    except Exception as e:
        print("Error al copiar el ejecutable: {}".format(e))
        return None

def _es_windows_xp():
    return platform.system() == "Windows" and platform.release() == "XP"

def _get_startup_folder(todos_usuarios=False):
    """Obtiene la carpeta Startup correcta según idioma y alcance."""
    if platform.system() != "Windows":
        return None
    try:
        CSIDL_STARTUP = 7
        CSIDL_COMMON_STARTUP = 0x0018
        folder_id = CSIDL_COMMON_STARTUP if todos_usuarios else CSIDL_STARTUP
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, folder_id, None, 0, buf)
        return buf.value
    except Exception:
        if todos_usuarios:
            return r"C:\Documents and Settings\All Users\Menú Inicio\Programas\Inicio"
        else:
            return os.path.join(
                os.environ.get("USERPROFILE", ""),
                "Menú Inicio",
                "Programas",
                "Inicio"
            )

def _crear_bat_en_startup(ruta_ejecutable, todos_usuarios=False):
    if platform.system() != "Windows":
        return False
    startup_dir = _get_startup_folder(todos_usuarios=todos_usuarios)
    if not startup_dir:
        print("No se pudo obtener la carpeta de inicio.")
        return False
    bat_path = os.path.join(startup_dir, "ClienteMonitoreo.bat")
    ruta_abs = os.path.abspath(ruta_ejecutable)
    try:
        if not os.path.exists(startup_dir):
            os.makedirs(startup_dir)
        elif not os.path.isdir(startup_dir):
            print("¡Advertencia! La ruta de Startup no es un directorio: {}".format(startup_dir))
            return False
        with open(bat_path, "w") as f:
            f.write("@echo off\n")
            f.write('cd /d "{}"\n'.format(os.path.dirname(ruta_abs)))
            f.write('"{}"\n'.format(ruta_abs))
        print("Archivo .bat creado en Startup: {}".format(bat_path))
        return True
    except Exception as e:
        print("Error al crear .bat en Startup: {}".format(str(e)))
        return False

def _registrar_con_schtasks(horas, ruta_ejecutable):
    try:
        task_name = "ClienteMonitoreoLocal"
        try:
            subprocess.check_call(
                ["schtasks", "/delete", "/tn", task_name, "/f"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError:
            pass
        if horas >= 24 and horas % 24 == 0:
            dias = horas // 24
            cmd = [
                "schtasks", "/create",
                "/tn", task_name,
                "/tr", ruta_ejecutable,
                "/sc", "daily",
                "/mo", str(dias),
                "/ru", "SYSTEM",
                "/rl", "HIGHEST",
                "/f"
            ]
        else:
            minutos = horas * 60
            cmd = [
                "schtasks", "/create",
                "/tn", task_name,
                "/tr", ruta_ejecutable,
                "/sc", "once",
                "/st", "00:00",
                "/ri", str(minutos),
                "/du", "9999:00",
                "/ru", "SYSTEM",
                "/rl", "HIGHEST",
                "/f"
            ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            print("Error schtasks: {}".format(stderr.strip()))
            return False
        print("Tarea '{}' creada (cada {}h) para todos los usuarios.".format(task_name, horas))
        return True
    except Exception as e:
        print("Excepción en schtasks: {}".format(str(e)))
        return False

def _registrar_crontab_linux(horas, ruta_ejecutable):
    if not es_admin():
        print("Advertencia: sin root, la tarea solo aplica al usuario actual.")
        try:
            cron_line = "0 */{} * * * cd {} && {} >> {} 2>&1".format(
                horas, os.path.dirname(ruta_ejecutable), ruta_ejecutable, ConfigManager().log_file
            )
            crontab_actual = subprocess.check_output(["crontab", "-l"], stderr=subprocess.STDOUT).decode("utf-8")
        except subprocess.CalledProcessError:
            crontab_actual = ""
        nuevas_lineas = [line for line in crontab_actual.splitlines() if "ClienteMonitoreoLocal" not in line]
        nuevas_lineas.extend(["# ClienteMonitoreoLocal - Auto-generado", cron_line])
        tmp_file = "/tmp/crontab.csi"
        with open(tmp_file, "w") as f:
            f.write("\n".join(nuevas_lineas) + "\n")
        subprocess.check_call(["crontab", tmp_file])
        os.remove(tmp_file)
        return True
    else:
        cron_file = "/etc/cron.d/cliente_monitoreo"
        cron_line = "0 */{} * * * root cd {} && {} >> {} 2>&1".format(
            horas, os.path.dirname(ruta_ejecutable), ruta_ejecutable, ConfigManager().log_file
        )
        try:
            with open(cron_file, "w") as f:
                f.write("# ClienteMonitoreoLocal - Global\n")
                f.write(cron_line + "\n")
            os.chmod(cron_file, 0o644)
            print("Crontab global creado en /etc/cron.d/")
            return True
        except Exception as e:
            print("Error al crear crontab global: {}".format(str(e)))
            return False

def registrar_tarea_programada():
    config = ConfigManager()
    conf = config.cargar_configuracion()
    if not conf:
        print("No hay configuración. Ejecute el escaneo primero.")
        return False
    horas = int(conf.get("horas_tarea", 24))
    if horas < 1:
        horas = 24
    ruta_instalada = _copiar_ejecutable_a_config()
    if not ruta_instalada:
        print("Advertencia: no se pudo copiar el ejecutable. Usando ruta actual.")
        ruta_instalada = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    system = platform.system().lower()
    if system == "windows":
        if _es_windows_xp():
            if _copiar_ejecutable_a_config():
                ruta_instalada = _get_ruta_instalada()
                _crear_bat_en_startup(ruta_instalada, todos_usuarios=True)
                print("Modo XP: Tarea configurada para TODOS los usuarios.")
            return True
        else:
            return _registrar_con_schtasks(horas, ruta_instalada)
    elif system == "linux":
        return _registrar_crontab_linux(horas, ruta_instalada)
    else:
        print("Sistema no soportado para tareas programadas.")
        return False