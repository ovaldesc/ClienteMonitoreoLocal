# utils/scheduler.py

import os
import sys
import shutil
import subprocess
import platform
from .config_manager import ConfigManager

def _get_ruta_instalada():
    """Devuelve la ruta donde se copiará el ejecutable instalado (sin espacios)."""
    config = ConfigManager()
    if getattr(sys, 'frozen', False):
        exe_name = "ClienteMonitoreo.exe" if platform.system() == "Windows" else "ClienteMonitoreo"
        return os.path.join(config.config_dir, exe_name)
    else:
        return os.path.join(config.config_dir, "main.py")

def _copiar_ejecutable_a_config():
    """Copia el ejecutable actual (o main.py) a la carpeta de configuración."""
    destino = _get_ruta_instalada()
    if os.path.exists(destino):
        return destino  # Ya existe

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

def _registrar_con_at(horas, ruta_ejecutable):
    try:
        intervalo = min(horas, 6)
        for i in range(0, 24, intervalo):
            hora = "{:02d}:00".format(i)
            cmd = ["at", hora, "/every:M,T,W,Th,F,S,Su", ruta_ejecutable]
            subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Tarea creada en Windows XP (cada ~{}h)".format(intervalo))
        return True
    except Exception as e:
        print("Error con 'at': {}".format(str(e)))
        return False

def _registrar_con_schtasks(horas, ruta_ejecutable):
    try:
        cmd_tr = ruta_ejecutable
        task_name = "ClienteMonitoreoLocal"

        # Eliminar tarea anterior
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
                "/tr", cmd_tr,
                "/sc", "daily",
                "/mo", str(dias),
                "/f"
            ]
        else:
            minutos = horas * 60
            cmd = [
                "schtasks", "/create",
                "/tn", task_name,
                "/tr", cmd_tr,
                "/sc", "once",
                "/st", "00:00",
                "/ri", str(minutos),
                "/du", "9999:00",
                "/f"
            ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
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
            return _registrar_con_at(horas, ruta_instalada)
        else:
            return _registrar_con_schtasks(horas, ruta_instalada)
    elif system == "linux":
        return _registrar_crontab_linux(horas, ruta_instalada)
    else:
        print("Sistema no soportado para tareas programadas.")
        return False