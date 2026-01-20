# utils/config_manager.py

import os
import json
import platform
import hashlib
import uuid
from datetime import datetime
from utils.aes_puro import _aes_cbc_encrypt, _aes_cbc_decrypt

def _get_config_dir():
    """Ruta de configuración global (accesible por todos los usuarios)."""
    system = platform.system().lower()
    if system == "windows":
        # Windows XP: C:\Documents and Settings\All Users\Application Data
        all_users = os.environ.get("ALLUSERSPROFILE", r"C:\Documents and Settings\All Users")
        return os.path.join(all_users, "Application Data", "ClienteMonitoreoLocal")
    elif system == "linux":
        return "/etc/ClienteMonitoreoLocal"
    else:
        raise OSError("Sistema no soportado")

def _get_data_dir():
    """Ruta para datos variables (logs, informes pendientes)."""
    system = platform.system().lower()
    if system == "windows":
        all_users = os.environ.get("ALLUSERSPROFILE", r"C:\Documents and Settings\All Users")
        return os.path.join(all_users, "Application Data", "ClienteMonitoreoLocal")
    elif system == "linux":
        return "/var/lib/ClienteMonitoreoLocal"
    else:
        raise OSError("Sistema no soportado")

def _get_config_file():
    return os.path.join(_get_config_dir(), "config.csi")

def _get_log_file():
    return os.path.join(_get_data_dir(), "CSI.log")

def _generar_clave_128():
    try:
        mac = hex(uuid.getnode())[2:].zfill(12)[-12:]
        hostname = platform.node()
        semilla = (mac + hostname).encode('utf-8')
        return hashlib.sha256(semilla).digest()[:16]
    except Exception:
        return b'csi_fallback_key_128'

class ConfigManager:
    def __init__(self):
        self.config_dir = _get_config_dir()
        self.data_dir = _get_data_dir()
        self.config_file = _get_config_file()
        self.log_file = _get_log_file()
        self._crear_directorio()

    def _crear_directorio(self):
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

    def guardar_configuracion(self, ip_servidor, horas_tarea, ultima_ejecucion=None):
        datos = {
            "ip_servidor": ip_servidor,
            "horas_tarea": horas_tarea,
            "log_path": self.log_file,
            "fecha_guardado": datetime.now().isoformat(),
            "ultima_ejecucion": ultima_ejecucion or datetime.now().isoformat(),
        }
        datos_bytes = json.dumps(datos, ensure_ascii=False).encode('utf-8')
        clave = _generar_clave_128()
        cifrado = _aes_cbc_encrypt(datos_bytes, clave)
        with open(self.config_file, "wb") as f:
            f.write(cifrado)

    def cargar_configuracion(self):
        if not os.path.exists(self.config_file):
            return None
        with open(self.config_file, "rb") as f:
            cifrado = f.read()
        clave = _generar_clave_128()
        plano = _aes_cbc_decrypt(cifrado, clave)
        return json.loads(plano.decode('utf-8'))

    def get_rutas(self):
        return {
            "config_dir": self.config_dir,
            "data_dir": self.data_dir,
            "config_file": self.config_file,
            "log_file": self.log_file,
        }