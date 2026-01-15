# main.py (MODIFICADO)

import sys
import os
from datetime import datetime, timedelta
from utils.log_redirect import start_logging, stop_logging
from utils.config_manager import ConfigManager
from utils.token_manager import token_manager
from utils.scheduler import registrar_tarea_programada
from services.recoleccion import recolectar_datos_completos
from services.reporte import generar_informe, procesar_informes_pendientes
from services.servidor import ClienteServidor
from utils.config_interactiva import pedir_configuracion_inicial
from utils.consola import ocultar_consola_si_no_interactiva
from utils.auto_actualizacion import auto_actualizar_si_necesario

def _debe_ejecutarse(conf):
    """Devuelve True si ya pasó el tiempo necesario desde la última ejecución."""
    horas = int(conf.get("horas_tarea", 24))
    ultima_str = conf.get("ultima_ejecucion")
    if not ultima_str:
        return True
    try:
        ultima = datetime.fromisoformat(ultima_str)
    except:
        return True
    ahora = datetime.now()
    if horas >= 24:
        dias_requeridos = max(1, horas // 24)
        dias_pasados = (ahora.date() - ultima.date()).days
        return dias_pasados >= dias_requeridos
    else:
        delta = ahora - ultima
        horas_pasadas = delta.total_seconds() / 3600
        return horas_pasadas >= horas

def main():
    config_mgr = ConfigManager()
    token_manager.set_ruta(config_mgr.config_dir)
    auto_actualizar_si_necesario()

    if "--reconfigurar" in sys.argv:
        print('Modo reconfiguración activado')
        if os.path.exists(config_mgr.config_file):
            os.remove(config_mgr.config_file)
        print("Configuración anterior eliminada.")
        token_manager.eliminar_token()
        print("Token anterior eliminado.")
        conf = None
    else:
        conf = config_mgr.cargar_configuracion()

    if not conf:
        servidor, horas = pedir_configuracion_inicial()
        config_mgr.guardar_configuracion(servidor, horas)
        registrar_tarea_programada()
        _, instancias, ip_local = recolectar_datos_completos()
        cliente = ClienteServidor(servidor)
        token = cliente.registrar_equipo(instancias["sistema"].obtener_nombre_pc(), ip_local)
        if token:
            token_manager.guardar_token(token, instancias["sistema"].obtener_nombre_pc(), ip_local)
            print("Equipo registrado exitosamente en el servidor.")
        else:
            print("Error: No se pudo registrar el equipo en el servidor.")
    else:
        # ✅ NUEVO: Verificación de frecuencia antes de ejecutar
        if not _debe_ejecutarse(conf):
            print("No es momento de ejecutar (según configuración). Saliendo.")
            return  # Salir sin hacer nada

        # Actualizar última ejecución ANTES de recolectar
        config_mgr.guardar_configuracion(
            conf["ip_servidor"],
            conf["horas_tarea"],
            ultima_ejecucion=datetime.now().isoformat()
        )

        servidor = conf["ip_servidor"]
        cliente = ClienteServidor(servidor)
        procesar_informes_pendientes(cliente)
        datos, _, _ = recolectar_datos_completos()
        resultado = generar_informe(cliente, datos)
        print("Resultado del informe: {}".format(resultado))

if __name__ == "__main__":
    ocultar_consola_si_no_interactiva()
    logger = start_logging("CSI.log")
    try:
        main()
    except KeyboardInterrupt:
        print("\nEjecución cancelada por el usuario.")
    except Exception as e:
        print("Error crítico: {}".format(e))
    finally:
        stop_logging()