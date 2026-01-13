# sistema/windows/antivirus_info.py
import os
import re
import winreg
import subprocess
import tempfile


class AntivirusInfoWindows:

    # Patrones regex precompilados para mejor performance
    VERSION_PATTERN = re.compile(r"Versión (\d+\.\d+\.\d+)")
    LICENSE_PATTERN = re.compile(r"Autorizado a: (.+?)\. Fecha de expiración: (.+)")

    def __init__(self):
        self.log_paths = (
            r"C:\ProgramData\Segurmatica\Segurmatica Antivirus\Client\System.log",
            r"C:\Documents and Settings\All Users\Datos de programa\Segurmatica\Segurmatica Antivirus\Client\System.log",
        )

    def _find_log_file(self):
        """Encuentra la ruta del archivo log válido."""
        for path in self.log_paths:
            if os.path.exists(path):
                return path
        return None

    def get_segurmatica_info(self):
        """Obtiene la información del antivirus Segurmatica."""
        info = {
            "Version": None,
            "Conexión exitosa al servidor": None,
            "Licencia Corporativa": None,
            "Licencia": None,
            "Fecha de expiración": None,
            "Fecha de actualización": None,
            "Protección permanente": None,
            "Resultado de la última búsqueda de código Maligno": None,
        }

        log_file = self._find_log_file()
        if not log_file:
            return {
                "mensaje": "Antivirus Segurmatica no está instalado en el dispositivo"
            }

        try:
            with open(log_file, "r", encoding="latin-1") as file:
                self._process_log_file(file, info)
        except (IOError, UnicodeDecodeError) as e:
            print("Error al procesar el archivo log: {}".format(str(e)))
            return {
                "mensaje": "Antivirus Segurmatica no está instalado en el dispositivo"
            }

        # Verificar si realmente se obtuvo información (si todos los valores son None, no está instalado)
        if all(value is None for value in info.values()):
            return {
                "mensaje": "Antivirus Segurmatica no está instalado en el dispositivo"
            }

        return info

    def get_kaspersky_info(self):
        kaspersky_info = {
            "Version de Kaspersky": None,
            "Estado de Actualizacion": None,
            "Fecha de Actualizacion": None,
            "Protección de control activada": None,
            "Licencia": None,
            "Control de dispositivos": None,
            "Unido a un KSC": False,
        }

        kaspersky_path = AntivirusInfoWindows.get_kaspersky_path()
        if not kaspersky_path:
            return {
                "mensaje": "Antivirus Kaspersky no está instalado en el dispositivo"
            }

        try:
            # Comprobamos el estado de diferentes componentes de Kaspersky
            stat_output = subprocess.check_output(
                [os.path.join(kaspersky_path, "avp.com"), "STATUS"],
                stderr=subprocess.STDOUT,
            ).decode("latin1")
            for line in stat_output.splitlines():
                if "Protection " in line:
                    kaspersky_info["Protección de control activada"] = line.split()[
                        -1
                    ].strip()
                if "DeviceControl " in line:
                    kaspersky_info["Control de dispositivos"] = line.split()[-1].strip()
        except subprocess.CalledProcessError as e:
            print("Error al ejecutar el comando avp.com STATUS: {}".format(str(e)))

        try:
            # Comprobamos el estado de diferentes componentes de Kaspersky
            stat_output = subprocess.check_output(
                [os.path.join(kaspersky_path, "avp.com"), "?"],
                stderr=subprocess.STDOUT,
            ).decode("latin1")
            for line in stat_output.splitlines():
                if "Kaspersky Application" in line:
                    kaspersky_info["Version de Kaspersky"] = line.split()[-1].strip()
        except subprocess.CalledProcessError as e:
            print("Error al ejecutar el comando avp.com ?: {}".format(str(e)))

        try:
            # Crear un archivo por lotes temporal para ejecutar el comando LICENSE /CHECK
            with tempfile.NamedTemporaryFile(delete=False, suffix=".bat") as bat_file:
                bat_file.write(
                    '@echo off\n"{}" LICENSE /CHECK\n'.format(
                        os.path.join(kaspersky_path, "avp.com")
                    ).encode("latin1")
                )
                bat_file.write(b"@echo on\n")
                bat_file.close()

                # Ejecutar el archivo por lotes temporal
                stat_output_license = subprocess.check_output(
                    [bat_file.name], stderr=subprocess.STDOUT
                ).decode("latin1")
                os.remove(bat_file.name)

            for line in stat_output_license.splitlines():
                if "License ID" in line:
                    kaspersky_info["Licencia"] = line.split(": ", 1)[1].strip()
        except subprocess.CalledProcessError as e:
            print(
                "Error al ejecutar el comando avp.com LICENSE /CHECK: {}".format(str(e))
            )

        try:
            finalizado = "Desconocido"
            completado = "0%"

            # Obtenemos estadísticas del actualizador
            stat_output_updater = subprocess.check_output(
                [os.path.join(kaspersky_path, "avp.com"), "STATISTICS", "Updater"],
                stderr=subprocess.STDOUT,
            ).decode("latin1")
            for line in stat_output_updater.splitlines():
                if "Time Finish:" in line:
                    finalizado = line.split(": ", 1)[1].strip()
                if "Completion:" in line:
                    completado = line.split(": ", 1)[1].strip()

            if completado == "100%":
                kaspersky_info["Estado de Actualizacion"] = "Actualizado"
                kaspersky_info["Fecha de Actualizacion"] = finalizado
            else:
                kaspersky_info["Estado de Actualizacion"] = "Desactualizado"
                kaspersky_info["Fecha de Actualizacion"] = finalizado

        except subprocess.CalledProcessError as e:
            print(
                "Error al ejecutar el comando avp.com STATISTICS Updater: {}".format(
                    str(e)
                )
            )

        try:
            # Ejecutar el comando 'tasklist' y capturar la salida
            resultado = subprocess.check_output(
                ["tasklist"], shell=True, universal_newlines=True
            )
            # Verificar si 'klnagent.exe' está presente en la salida
            kaspersky_info["Unido a un KSC"] = "klnagent.exe" in resultado.lower()
        except subprocess.CalledProcessError as e:
            print("Error al ejecutar el comando tasklist: {}".format(str(e)))
            kaspersky_info["Unido a un KSC"] = False

        # Verificar si realmente se obtuvo información (si la versión es None, no está instalado correctamente)
        if kaspersky_info["Version de Kaspersky"] is None:
            return {
                "mensaje": "Antivirus Kaspersky no está instalado en el dispositivo"
            }

        return kaspersky_info

    @staticmethod
    def get_kaspersky_path():
        try:
            # Claves de registro donde Kaspersky podría estar instalado
            reg_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\KasperskyLab",
            ]

            for reg_path in reg_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        try:
                            # Buscar por nombre de producto
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if "kaspersky" in display_name.lower():
                                # Intentar obtener la ruta de instalación
                                try:
                                    install_path = winreg.QueryValueEx(
                                        subkey, "InstallLocation"
                                    )[0]
                                    if install_path and os.path.exists(install_path):
                                        return install_path
                                except OSError:
                                    pass
                        except OSError:
                            continue
                except OSError:
                    continue

            # Si no se encuentra en el registro, buscar en las rutas comunes
            common_paths = [
                os.path.join(os.environ.get("ProgramFiles", ""), "Kaspersky Lab"),
                os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Kaspersky Lab"),
            ]

            for path in common_paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        if "avp.exe" in files:  # Ejecutable principal de Kaspersky
                            return root
        except Exception as e:
            print("Error al obtener la ruta de Kaspersky: {}".format(str(e)))
        return None

    def _process_log_file(self, file, info):
        """Procesa el archivo log línea por línea para extraer información."""
        start_time = None

        for line in file:
            line = line.strip()
            if not line:
                continue

            # Versión del antivirus
            if not info["Version"]:
                version_match = self.VERSION_PATTERN.search(line)
                if version_match:
                    info["Version"] = version_match.group(1)

            # Conexión al servidor
            if "Conexión exitosa al servidor" in line:
                info["Conexión exitosa al servidor"] = line.split(
                    "Conexión exitosa al servidor "
                )[-1]

            # Información de licencia
            if "Autorizado a:" in line and "Fecha de expiración:" in line:
                license_match = self.LICENSE_PATTERN.search(line)
                if license_match:
                    info["Licencia"], info["Fecha de expiración"] = (
                        license_match.groups()
                    )

            # Licencia corporativa
            if "Antivirus|Licencia corporativa" in line:
                info["Licencia Corporativa"] = line.split("|")[-1].strip()

            # Fecha de actualización
            if "Fecha de actualización" in line:
                info["Fecha de actualización"] = line.split(": ")[-1]

            # Protección permanente
            if "Protección permanente" in line:
                info["Protección permanente"] = line.split(": ")[-1]

            # Resultado de búsqueda
            if "Búsqueda|Inicio" in line:
                start_time = line.split("|")[0].strip()
            elif "Búsqueda|Fin" in line and "Objetos revisados" in line and start_time:
                objetos = line.split(": ")[-1].strip()
                info["Resultado de la última búsqueda de código Maligno"] = (
                    "{start_time} Objetos revisados: {objetos}".format(
                        start_time=start_time, objetos=objetos
                    )
                )
