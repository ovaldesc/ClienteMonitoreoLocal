# sistema/linux/red.py

import socket
import subprocess
import os
import glob
import re
from concurrent.futures import ThreadPoolExecutor


class RedLinux:
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
        Obtiene SOLO las carpetas compartidas por el usuario y del sistema (Samba).
        Devuelve una lista de diccionarios con el mismo formato que Windows.
        """
        shared_folders = []

        # =================== SAMBA - Carpetas compartidas por usuario ===================
        try:
            # Intentar obtener carpetas compartidas por el usuario con 'net usershare info'
            output = subprocess.check_output(
                ["net", "usershare", "info"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode()

            # Procesar la salida de net usershare info
            current_share = {}
            for line in output.split("\n"):
                line = line.strip()
                if line.startswith("["):
                    # Nueva carpeta compartida
                    if current_share and current_share.get("Ruta"):
                        shared_folders.append(current_share)
                    share_name = line.strip("[]")
                    current_share = {
                        "Nombre": share_name,
                        "Ruta": "",
                        "Descripción": "",
                        "Tipo": "Carpeta compartida (usuario)",
                    }
                elif line.startswith("path="):
                    current_share["Ruta"] = line.split("=", 1)[1].strip()
                elif line.startswith("comment="):
                    current_share["Descripción"] = line.split("=", 1)[1].strip()

            # Agregar la última carpeta si existe
            if current_share and current_share.get("Ruta"):
                shared_folders.append(current_share)
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            pass

        # =================== SAMBA - Carpetas compartidas del sistema ===================
        try:
            # Leer configuración de Samba desde /etc/samba/smb.conf
            if os.path.exists("/etc/samba/smb.conf"):
                with open("/etc/samba/smb.conf", "r") as f:
                    content = f.read()

                # Verificar si Samba está activo
                try:
                    samba_status = (
                        subprocess.check_output(
                            ["systemctl", "is-active", "smbd"],
                            stderr=subprocess.DEVNULL,
                        )
                        .decode()
                        .strip()
                    )
                    if samba_status == "active":
                        # Parsear smb.conf para encontrar secciones [share]
                        share_pattern = r"\[([^\]]+)\]\s*(.*?)(?=\[|$)"
                        matches = re.findall(share_pattern, content, re.DOTALL)

                        for share_name, share_config in matches:
                            # Ignorar secciones especiales
                            if share_name.lower() in [
                                "global",
                                "homes",
                                "printers",
                                "print$",
                            ]:
                                continue

                            # Extraer path y comment
                            path_match = re.search(
                                r"path\s*=\s*(.+)", share_config, re.IGNORECASE
                            )
                            comment_match = re.search(
                                r"comment\s*=\s*(.+)", share_config, re.IGNORECASE
                            )

                            path = path_match.group(1).strip() if path_match else ""
                            comment = (
                                comment_match.group(1).strip()
                                if comment_match
                                else "Sin descripción"
                            )

                            if path and os.path.exists(path):
                                shared_folders.append(
                                    {
                                        "Nombre": share_name,
                                        "Ruta": path,
                                        "Descripción": comment,
                                        "Tipo": "Carpeta compartida (sistema)",
                                    }
                                )
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
        except (IOError, PermissionError):
            pass

        # Asegurar que todas las carpetas tengan descripción
        for folder in shared_folders:
            if not folder.get("Descripción"):
                folder["Descripción"] = "Sin descripción"

        return shared_folders
