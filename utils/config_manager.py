# utils/config_manager.py

import os
import json
import platform
import hashlib
import uuid
from datetime import datetime
from utils.aes_puro import _aes_cbc_encrypt, _aes_cbc_decrypt

def _get_config_dir():
    system = platform.system().lower()
    if system == "windows":
        # ✅ SIN ESPACIOS en el nombre de la carpeta
        return os.path.join(os.environ.get("APPDATA", ""), "ClienteMonitoreoLocal")
    elif system == "linux":
        return os.path.join(os.path.expanduser("~"), ".config", "ClienteMonitoreoLocal")
    else:
        raise OSError("Sistema no soportado")

def _get_config_file():
    return os.path.join(_get_config_dir(), "config.csi")

def _get_log_file():
    return os.path.join(_get_config_dir(), "CSI.log")

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
        self.config_file = _get_config_file()
        self.log_file = _get_log_file()
        self._crear_directorio()

    def _crear_directorio(self):
        os.makedirs(self.config_dir, exist_ok=True)

    def guardar_configuracion(self, ip_servidor, horas_tarea):
        datos = {
            "ip_servidor": ip_servidor,
            "horas_tarea": horas_tarea,
            "log_path": self.log_file,
            "fecha_guardado": datetime.now().isoformat(),
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
            "config_file": self.config_file,
            "log_file": self.log_file,
        }