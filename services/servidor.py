# services/servidor.py
import requests
import json
from datetime import datetime
from utils.token_manager import token_manager
from utils.hash_utils import calcular_hash_datos


class ClienteServidor:
    def __init__(self, url_base):
        # Asegurar que la URL no termine en /
        self.url_base = url_base.rstrip("/")
        self.timeout = 30

    def registrar_equipo(self, nombre_equipo, ip_equipo):
        """Registra el equipo y obtiene un token"""
        try:
            payload = {
                "nombre_equipo": nombre_equipo,
                "ip_equipo": ip_equipo,
                "datos_sistema": {},  # El servidor puede ignorar esto si no lo necesita
            }

            session = requests.Session()
            session.trust_env = False

            response = session.post(
                "{}/api/registro/".format(self.url_base),
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 201:
                respuesta = response.json()
                token = respuesta.get("token")

                # Guardar token
                token_manager.guardar_token(token, nombre_equipo, ip_equipo)
                print("Equipo registrado exitosamente: {}".format(nombre_equipo))
                print("Token guardado: {}...".format(token[:10]))
                return token  # Devuelve el token para que main.py lo use si quiere
            else:
                print("Error al registrar el equipo: {}".format(response.status_code))
                return None

        except Exception as e:
            print("Excepción en registrar_equipo: {}".format(str(e)))
            return None

    def obtener_hash_ultimo_informe(self, token):
        """Obtiene el hash del último informe del equipo desde el servidor"""
        try:
            session = requests.Session()
            session.trust_env = False

            response = session.get(
                "{}/api/informes/hash/".format(self.url_base),
                timeout=self.timeout,
                headers={
                    "X-Equipo-Token": token,
                },
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print("Error al obtener el hash del último informe: {}".format(str(e)))
            return None

    def enviar_informe(self, datos_informe):
        """Envía el informe usando el token del equipo. Verifica cambios antes de enviar."""
        try:
            # Extraer nombre e IP una sola vez
            nombre_equipo = datos_informe.get("Nombre PC", "Desconocido")
            ip_equipo = datos_informe.get("IP", "Desconocida")

            # Obtener token
            token = token_manager.obtener_token()

            if not token:
                print("Token no encontrado, registrando equipo")
                if not self.registrar_equipo(nombre_equipo, ip_equipo):
                    return False
                token = token_manager.obtener_token()

            # Calcular hash del nuevo informe
            hash_nuevo = calcular_hash_datos(datos_informe)

            # Obtener hash del último informe del servidor
            hash_info = self.obtener_hash_ultimo_informe(token)

            if hash_info and hash_info.get("existe"):
                hash_anterior = hash_info.get("hash_datos")
                if hash_anterior == hash_nuevo:
                    return "sin_cambios"

            # Crear payload usando las variables ya extraídas
            payload = {
                "fecha_envio": datetime.now().strftime("%d/%m/%y %H:%M:%S"),
                "datos_sistema": datos_informe,
                "nombre_equipo": nombre_equipo,
                "ip_equipo": ip_equipo,
                "hash_datos": hash_nuevo,
            }

            session = requests.Session()
            session.trust_env = False

            response = session.post(
                "{}/api/informes/".format(self.url_base),
                json=payload,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "X-Equipo-Token": token,
                },
            )

            if response.status_code == 200:
                respuesta_json = response.json()
                if respuesta_json.get("actualizado"):
                    return "actualizado"
                else:
                    return "creado"
            elif response.status_code in (401, 403):
                # Token inválido, intentar re-registro
                print("Token inválido, intentando re-registro")
                token_manager.eliminar_token()
                if self.registrar_equipo(nombre_equipo, ip_equipo):
                    return self.enviar_informe(datos_informe)
                return False
            else:
                print("Error al enviar informe: código {}".format(response.status_code))
                return False

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False
        except Exception as e:
            print("Excepción en enviar_informe: {}".format(str(e)))
            return False

    def verificar_conexion(self):
        """Verifica la conexión con el servidor"""
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.get("{}/api/health".format(self.url_base), timeout=10)
            return response.status_code == 200
        except:
            return False