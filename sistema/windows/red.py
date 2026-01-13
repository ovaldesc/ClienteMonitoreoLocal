# sistemas/windows/red.py

import socket
import wmi
from concurrent.futures import ThreadPoolExecutor


class RedWindows:
    def scan_ports(self, host, start_port=1, end_port=1024):
        open_ports = []

        def scan(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    try:
                        service_name = socket.getservbyport(port)
                    except:
                        service_name = "Unknown"
                    open_ports.append((port, service_name))

        with ThreadPoolExecutor(max_workers=100) as executor:
            for port in range(start_port, end_port + 1):
                executor.submit(scan, port)
        return open_ports

    def get_carpetas_compartidas(self):
        """
        Obtiene SOLO las carpetas compartidas manualmente por el usuario (no recursos administrativos).
        Filtra por Type = 0 (Disco Lógico, creado por el usuario).
        """
        try:
            c = wmi.WMI()
            shared_folders = []

            for share in c.Win32_Share():
                # Filtrar solo carpetas compartidas por el usuario (Type == 0)
                if share.Type == 0 and share.Path:
                    shared_folders.append(
                        {
                            "Nombre": share.Name,
                            "Ruta": share.Path,
                            "Descripción": share.Description or "Sin descripción",
                            "Tipo": "Carpeta compartida (usuario)",
                        }
                    )
            return shared_folders
        except Exception as e:
            print(
                "Error al obtener las carpetas compartidas con wmic: {}".format(str(e))
            )
            return []
