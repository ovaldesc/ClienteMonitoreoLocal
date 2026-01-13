# main.py

import sys
import os
from utils.log_redirect import start_logging, stop_logging
from utils.config_manager import ConfigManager
from utils.token_manager import token_manager
from utils.scheduler import registrar_tarea_programada
from services.recoleccion import recolectar_datos_completos
from services.reporte import generar_informe, procesar_informes_pendientes
from services.servidor import ClienteServidor
from utils.config_interactiva import pedir_configuracion_inicial
from utils.consola import ocultar_consola_si_no_interactiva

def main():
    config_mgr = ConfigManager()
    token_manager.set_ruta(config_mgr.config_dir)

    from utils.auto_actualizacion import auto_actualizar_si_necesario
    auto_actualizar_si_necesario()
    
    # >>> NUEVO: Auto-actualización <<<
    # Modo reconfiguración
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
        # Primera ejecución
        servidor, horas = pedir_configuracion_inicial()
        config_mgr.guardar_configuracion(servidor, horas)
        registrar_tarea_programada()

        # Recolectar IP local y registrar en servidor
        _, instancias, ip_local = recolectar_datos_completos()
        cliente = ClienteServidor(servidor)
        token = cliente.registrar_equipo(instancias["sistema"].obtener_nombre_pc(), ip_local)
        if token:
            token_manager.guardar_token(token, instancias["sistema"].obtener_nombre_pc(), ip_local)
            print("Equipo registrado exitosamente en el servidor.")
        else:
            print("Error: No se pudo registrar el equipo en el servidor.")
    else:
        # Ejecución normal
        servidor = conf["ip_servidor"]
        cliente = ClienteServidor(servidor)
        procesar_informes_pendientes(cliente)
        datos, _, _ = recolectar_datos_completos()
        resultado = generar_informe(cliente, datos)
        print("Resultado del informe: {}".format(resultado))

if __name__ == "__main__":
    ocultar_consola_si_no_interactiva()  # ← mover esta función a utils/consola.py
    logger = start_logging("CSI.log")
    try:
        main()
    except KeyboardInterrupt:
        print("\nEjecución cancelada por el usuario.")
    except Exception as e:
        print("Error crítico: {}".format(e))
    finally:
        stop_logging()