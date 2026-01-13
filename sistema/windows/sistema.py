# sistema/windows/sistema.py
import socket
import datetime
import winreg
import unicodedata
import subprocess
import re


class SistemaWindows:

    salida_systeminfo = None

    def parse_systeminfo_from_cmd(self):
        """
        Ejecuta systeminfo y extrae:
        - hostname
        - os_name
        - os_version
        - system_type
        - primera direccion IPv4

        Retorna un dict con esos valores.
        """
        output = self.get_systeminfo()
        if not output:
            return {}

        lines = output.splitlines()
        info = {
            'hostname': None,
            'os_name': None,
            'os_version': None,
            'system_type': None,
            'ip_address': None
        }

        for line in lines:
            line = line.rstrip()
            if line.startswith("Nombre de host:"):
                info['hostname'] = line.split(":", 1)[1].strip()
            elif line.startswith("Nombre del sistema operativo:"):
                info['os_name'] = line.split("Microsoft", 1)[1].strip()
            elif line.startswith("Versión del sistema operativo:"):
                line = line.split(":", 1)[1].strip()
                info['os_version'] = line.split(" ", 1)[0].strip()
            elif line.startswith("Tipo de sistema:"):
                line = line.split(":", 1)[1].strip()
                info['system_type'] = line.split("-", 1)[0].strip()

        # Buscar la primera direccion IPv4 valida
        in_network = False
        ip_pattern = re.compile(r'\[\d+\]:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')

        for line in lines:
            line = line.rstrip()
            if line.startswith("Tarjeta(s) de red:"):
                in_network = True
                continue
            if in_network:
                match = ip_pattern.search(line)
                if match:
                    info['ip_address'] = match.group(1)
                    break  # Solo la primera IPv4

        return info

    def get_systeminfo(self):
        """
        Ejecuta 'systeminfo' en Windows y devuelve la salida como cadena de texto.
        Maneja la codificacion tipica del CMD en sistemas en espanol.
        """
        try:
            result = subprocess.check_output("chcp 65001 >nul && systeminfo", shell=True)

            # Intentar decodificar con codificaciones comunes en Windows en espanol
            salida = result.decode('utf-8', errors='replace')
            return salida 

            # Si ninguna funciona, forzar decodificacion con errores reemplazados
           
            
        except subprocess.CalledProcessError as e:
            print("Error al ejecutar systeminfo: {}".format(str(e)))
            return "Error: {}".format(e)
    
    def obtener_nombre_pc(self):
        return socket.gethostname()

    def get_ip(self):
        if not self.salida_systeminfo :
            self.salida_systeminfo = self.parse_systeminfo_from_cmd()
        return self.salida_systeminfo['ip_address']

    def get_version_so(self):
        return "{} (Build {}) {}".format(
            self.salida_systeminfo['os_name'], self.salida_systeminfo['os_version'], self.salida_systeminfo['system_type']
        )

    def get_fecha_ejecucion(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_installed_apps(self):

        def _get_installed_apps_from_hive(hive, flag):
            software_list = []
            uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"

            try:
                with winreg.ConnectRegistry(None, hive) as reg:
                    with winreg.OpenKey(
                        reg, uninstall_key, 0, winreg.KEY_READ | flag
                    ) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        name = winreg.QueryValueEx(
                                            subkey, "DisplayName"
                                        )[0]
                                        system_component = self._get_reg_value(
                                            subkey, "SystemComponent", 0
                                        )

                                        if (
                                            system_component != 1
                                            and name
                                            and not name.startswith(
                                                ("KB", "Security Update for")
                                            )
                                            and not any(
                                                x in name
                                                for x in [
                                                    "Update for Windows",
                                                    "Service Pack",
                                                ]
                                            )
                                        ):

                                            version = self._get_reg_value(
                                                subkey, "DisplayVersion", "No version"
                                            )
                                            software_list.append((name, version))

                                    except (EnvironmentError, OSError):
                                        continue
                            except (EnvironmentError, OSError):
                                continue
            except (FileNotFoundError, PermissionError, OSError) as e:
                if isinstance(e, PermissionError):
                    print("Error de permisos: {}".format(str(e)))
                elif isinstance(e, FileNotFoundError):
                    print("Error de archivo no encontrado: {}".format(str(e)))
                elif isinstance(e, OSError):
                    print("Error de sistema operativo: {}".format(str(e)))
                return []

            return software_list

        hives = [
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY),
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_CURRENT_USER, 0),
        ]

        installed_apps = []
        for hive, flag in hives:
            installed_apps.extend(_get_installed_apps_from_hive(hive, flag))

        unique_apps = []
        seen_names = set()

        for name, version in installed_apps:
            if name not in seen_names:
                seen_names.add(name)
                unique_apps.append((name, version))

        return sorted(unique_apps, key=lambda x: x[0].lower())

    def _get_reg_value(self, key, value_name, default=None):
        try:
            return winreg.QueryValueEx(key, value_name)[0]
        except (EnvironmentError, OSError):
            return default
