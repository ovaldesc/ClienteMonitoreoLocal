# utils/token_manager.py
import os
import json
import uuid
import platform
import hashlib
from utils.aes_puro import _aes_cbc_encrypt, _aes_cbc_decrypt


def _generar_clave_128():
    try:
        mac = hex(uuid.getnode())[2:].zfill(12)[-12:]
        hostname = platform.node()
        semilla = (mac + hostname).encode('utf-8')
        return hashlib.sha256(semilla).digest()[:16]
    except Exception:
        return b'csi_fallback_key_128'

class TokenManager:
    def __init__(self):
        # Ruta configurada por ConfigManager en main (o por defecto)
        self._ruta = None

    def set_ruta(self, ruta):
        """Establece la carpeta donde guardar .csi_token"""
        self._ruta = ruta
        self.token_file = os.path.join(ruta, ".csi_token")

    def guardar_token(self, token, nombre_equipo, ip_equipo):
        try:
            datos = {
                "token": token,
                "nombre_equipo": nombre_equipo,
                "ip_equipo": ip_equipo,
            }
            datos_bytes = json.dumps(datos, ensure_ascii=False).encode('utf-8')
            clave = _generar_clave_128()
            cifrado = _aes_cbc_encrypt(datos_bytes, clave)
            with open(self.token_file, "wb") as f:
                f.write(cifrado)
            try:
                os.chmod(self.token_file, 0o600)
            except (OSError, PermissionError):
                pass
            return True
        except Exception as e:
            print("Error al guardar el token cifrado: {}".format(str(e)))
            return False

    def obtener_token(self):
        try:
            if not os.path.exists(self.token_file):
                return None
            with open(self.token_file, "rb") as f:
                cifrado = f.read()
            clave = _generar_clave_128()
            plano = _aes_cbc_decrypt(cifrado, clave)
            datos = json.loads(plano.decode('utf-8'))
            return datos.get("token")
        except Exception as e:
            print("Error al obtener el token cifrado: {}".format(str(e)))
            return None

    def obtener_info_equipo(self):
        try:
            if not os.path.exists(self.token_file):
                return None, None
            with open(self.token_file, "rb") as f:
                cifrado = f.read()
            clave = _generar_clave_128()
            plano = _aes_cbc_decrypt(cifrado, clave)
            datos = json.loads(plano.decode('utf-8'))
            return datos.get("nombre_equipo"), datos.get("ip_equipo")
        except Exception:
            return None, None

    def eliminar_token(self):
        try:
            if os.path.exists(self.token_file):
                os.unlink(self.token_file)
            return True
        except Exception:
            return False

token_manager = TokenManager()