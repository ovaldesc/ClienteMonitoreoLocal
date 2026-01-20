# services/reporte.py

import os
import json
import time
from datetime import datetime
from utils.config_manager import ConfigManager
from .servidor import ClienteServidor

def _get_pendientes_dir():
    config = ConfigManager()
    # ✅ Usar data_dir para datos variables
    return os.path.join(config.data_dir, "Informes_Pendientes")

def guardar_informe_local(datos):
    try:
        pendientes_dir = _get_pendientes_dir()
        os.makedirs(pendientes_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = "pendiente_{}.json".format(timestamp)
        ruta = os.path.join(pendientes_dir, nombre_archivo)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        return ruta
    except Exception as e:
        print("Error al guardar informe local: {}".format(str(e)))
        return None

def cargar_informes_pendientes():
    pendientes_dir = _get_pendientes_dir()
    if not os.path.exists(pendientes_dir):
        return []
    archivos = [os.path.join(pendientes_dir, f) for f in os.listdir(pendientes_dir) if f.endswith(".json")]
    archivos.sort()
    informes = []
    for f in archivos:
        try:
            with open(f, "r", encoding="utf-8") as file:
                datos = json.load(file)
                informes.append((f, datos))
        except:
            pass
    return informes

def eliminar_informe_pendiente(ruta):
    try:
        os.remove(ruta)
    except:
        pass

def enviar_con_reintentos(cliente, datos):
    reintentos = [(0, "inmediato"), (60, "1 min"), (90, "2 min"), (180, "3 min")]
    for i, (espera, desc) in enumerate(reintentos):
        if i > 0:
            print("Reintentando en {}...".format(desc))
            time.sleep(espera)
        resultado = cliente.enviar_informe(datos)
        if resultado in ("creado", "actualizado", "sin_cambios"):
            return resultado
    return "fallo_permanente"

def generar_informe(cliente, datos):
    try:
        resultado = enviar_con_reintentos(cliente, datos)
        if resultado != "fallo_permanente":
            return resultado
        else:
            ruta = guardar_informe_local(datos)
            if ruta:
                return "creado_local"
            return "error"
    except Exception as e:
        ruta = guardar_informe_local(datos)
        if ruta:
            return "creado_local"
        return "error"

def procesar_informes_pendientes(cliente):
    """Envía todos los informes pendientes antes de generar uno nuevo."""
    informes = cargar_informes_pendientes()
    if not informes:
        return
    print("Hay {} informes pendientes. Intentando enviar...".format(len(informes)))
    for ruta, datos in informes:
        resultado = enviar_con_reintentos(cliente, datos)
        if resultado in ("creado", "actualizado"):
            print("Informe pendiente enviado con éxito.")
            eliminar_informe_pendiente(ruta)
        elif resultado == "sin_cambios":
            print("Informe pendiente sin cambios. Eliminando.")
            eliminar_informe_pendiente(ruta)
        else:
            print("No se pudo enviar informe pendiente. Se mantendrá para el próximo intento.")