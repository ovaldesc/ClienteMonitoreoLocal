# utils/scheduler.py (MODIFICADO)

import os
import sys
import shutil
import subprocess
import platform
from .config_manager import ConfigManager
import ctypes
from ctypes import wintypes

def _get_ruta_instalada():
    config = ConfigManager()
    if getattr(sys, 'frozen', False):
        exe_name = "ClienteMonitoreo.exe" if platform.system() == "Windows" else "ClienteMonitoreo"
        return os.path.join(config.config_dir, exe_name)
    else:
        return os.path.join(config.config_dir, "main.py")

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

def _crear_bat_en_startup(ruta_ejecutable):
    if platform.system() != "Windows":
        return False
    """Obtiene la ruta real del Startup folder, independiente del idioma."""
    CSIDL_STARTUP = 7  # Constante de Windows para "Startup folder"
    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    try:
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_STARTUP, None, 0, buf)
        startup_dir = buf.value
    except Exception:
        startup_dir = os.path.join(
            os.environ.get("USERPROFILE", ""),
            "Menú Inicio",
            "Programas",
            "Inicio"
        )
    if not startup_dir or not os.path.isdir(os.path.dirname(startup_dir)):
        print("No se pudo determinar la carpeta de inicio.")
        return False
    
    bat_path = os.path.join(startup_dir, "ClienteMonitoreo.bat")
    ruta_abs = os.path.abspath(ruta_ejecutable)
    try:
        # Crear directorio solo si no existe (evita WinError 183 en XP)
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
                "/f"
            ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            print("Error schtasks: {}".format(stderr.strip()))
            return False
        print("Tarea '{}' creada (cada {}h)".format(task_name, horas))
        return True
    except Exception as e:
        print("Excepción en schtasks: {}".format(str(e)))
        return False

def _registrar_crontab_linux(horas, ruta_ejecutable):
    try:
        cron_line = "0 */{} * * * cd {} && {} >> {} 2>&1".format(
            horas, os.path.dirname(ruta_ejecutable), ruta_ejecutable, ConfigManager().log_file
        )
        try:
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
        print("Crontab actualizado (cada {}h)".format(horas))
        return True
    except Exception as e:
        print("Error en crontab: {}".format(str(e)))
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
            # ✅ NUEVO: Solo crea .bat en XP
            if _copiar_ejecutable_a_config():
                ruta_instalada = _get_ruta_instalada()
                _crear_bat_en_startup(ruta_instalada)
                print("Modo XP: Cliente configurado para ejecutarse desde Startup con control de frecuencia.")
            return True
        else:
            return _registrar_con_schtasks(horas, ruta_instalada)
    elif system == "linux":
        return _registrar_crontab_linux(horas, ruta_instalada)
    else:
        print("Sistema no soportado para tareas programadas.")
        return False