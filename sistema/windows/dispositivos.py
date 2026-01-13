# sistemas/windows/dispositivos.py
import subprocess
import tempfile
import os
import platform
from sistema.windows.antivirus_info import AntivirusInfoWindows
import re
import sys
import wmi


class DispositivoWindows:

    def get_dispositivos_conectados(self):
        """
        Obtiene dispositivos conectados en Windows: cámaras, impresoras, escáneres y discos.
        Clasifica los discos por tipo: Interno, Externo (USB), Removible, Óptico, etc.
        """

        def safe_str(val, default=""):
            return str(val if val is not None else default).strip()

        try:
            wmi_client = wmi.WMI()
            dispositivos = {
                "Cámaras": [],
                "Impresoras Activas": [],
                "Escáneres": [],
                "Discos": {
                    "Internos": [],
                    "Externos_USB": [],
                    "Removibles": [],
                    "Opticos": [],
                    "Desconocidos": [],
                },
            }

            # =================== CÁMARAS ===================
            for camara in wmi_client.Win32_PnPEntity():
                desc = safe_str(getattr(camara, "Description", "")).lower()
                status = safe_str(getattr(camara, "Status", ""))
                if desc and ("camera" in desc or "video" in desc) and status == "OK":
                    dispositivos["Cámaras"].append(
                        safe_str(getattr(camara, "Description", "")).title()
                    )

            # =================== IMPRESORAS ACTIVAS ===================
            virtual_printers = {
                "onenote",
                "xps",
                "pdf",
                "fax",
                "microsoft",
                "send to onenote",
                "pdfcreator",
                "bullzip",
                "cutepdf",
                "adobe pdf",
                "nitro pdf",
            }

            for impresora in wmi_client.Win32_Printer():
                name = safe_str(getattr(impresora, "Name", ""))
                work_offline = getattr(impresora, "WorkOffline", True)
                printer_status = getattr(impresora, "PrinterStatus", 0)
                port_name = safe_str(getattr(impresora, "PortName", "")).lower()

                # Filtramos impresoras virtuales y solo dejamos físicas
                is_virtual = any(
                    virtual in name.lower() for virtual in virtual_printers
                )
                is_network_printer = "\\" in port_name  # Impresoras de red

                if (
                    name
                    and not work_offline
                    and printer_status == 3
                    and not is_virtual
                    and not is_network_printer
                    and port_name not in ["nul:", "file:"]
                ):
                    dispositivos["Impresoras Activas"].append(name)

            # =================== ESCÁNERES ===================
            virtual_scanners = {
                "arsenal",
                "virtual",
                "mounter",
                "emulator",
                "simulator",
            }

            for escaner in wmi_client.Win32_PnPEntity():
                desc = safe_str(getattr(escaner, "Description", "")).lower()
                status = safe_str(getattr(escaner, "Status", ""))
                name = safe_str(getattr(escaner, "Name", "")).lower()
                pnpclass = safe_str(getattr(escaner, "PNPClass", "")).lower()

                # Filtramos escáneres virtuales
                is_scanner = (
                    "scanner" in desc
                    or "scan" in desc
                    or "image" in desc
                    or "scanner" in name
                    or "scan" in name
                    or "image" in name
                    or pnpclass == "image"
                )
                is_virtual = any(
                    virtual in desc for virtual in virtual_scanners
                ) or any(virtual in name for virtual in virtual_scanners)

                if is_scanner and status == "OK" and not is_virtual:
                    dispositivos["Escáneres"].append(
                        safe_str(getattr(escaner, "Description", "")).title()
                    )

            # =================== DISCOS (con clasificación) ===================
            for drive in wmi_client.Win32_DiskDrive():
                status = safe_str(getattr(drive, "Status", ""))
                if status != "OK":
                    continue

                model = safe_str(getattr(drive, "Model", ""))
                serial = safe_str(getattr(drive, "SerialNumber", ""))
                interface = safe_str(getattr(drive, "InterfaceType", "")).upper()
                media_type = safe_str(getattr(drive, "MediaType", "")).lower()
                description = safe_str(getattr(drive, "Description", "")).lower()
                size_bytes = getattr(drive, "Size", None)

                try:
                    size_gb = (
                        round(int(size_bytes) / (1000**3), 2)
                        if size_bytes and size_bytes.isdigit()
                        else "Desconocido"
                    )
                except (ValueError, TypeError, AttributeError):
                    size_gb = "Desconocido"

                # === Detectar tipo de disco ===
                disk_type = "Desconocidos"

                if "cdrom" in description or "dvd" in model or "optical" in media_type:
                    disk_type = "Opticos"
                elif interface == "USB":
                    if "flash" in model or "sd" in model or "card" in model:
                        disk_type = "Removibles"
                    else:
                        disk_type = "Externos_USB"
                elif interface in ["SATA", "IDE", "SCSI"] or "nvme" in model:
                    disk_type = "Internos"
                elif "removable" in media_type:
                    disk_type = "Removibles"
                else:
                    disk_type = "Desconocidos"

                # === Particiones ===
                particiones = []
                try:
                    for partition in drive.associators(
                        wmi_result_class="Win32_DiskPartition"
                    ):
                        for logical_disk in partition.associators(
                            wmi_result_class="Win32_LogicalDisk"
                        ):
                            particiones.append(
                                {
                                    "Letter": safe_str(
                                        getattr(logical_disk, "DeviceID", "N/A")
                                    ),
                                    "FileSystem": safe_str(
                                        getattr(logical_disk, "FileSystem", "N/A")
                                    ),
                                    "Type": getattr(logical_disk, "DriveType", 0),
                                    "SizeGB": (
                                        round(
                                            int(getattr(logical_disk, "Size", 0))
                                            / (1000**3),
                                            2,
                                        )
                                        if getattr(logical_disk, "Size", "0").isdigit()
                                        else 0
                                    ),
                                    "FreeSpaceGB": (
                                        round(
                                            int(getattr(logical_disk, "FreeSpace", 0))
                                            / (1000**3),
                                            2,
                                        )
                                        if getattr(
                                            logical_disk, "FreeSpace", "0"
                                        ).isdigit()
                                        else 0
                                    ),
                                }
                            )
                except Exception:
                    particiones.append({"Error": "No se pudieron leer las particiones"})

                # === Añadir disco ===
                disco_info = {
                    "Model": model or "Desconocido",
                    "SerialNumber": serial or "No disponible",
                    "InterfaceType": interface or "Desconocido",
                    "MediaType": media_type or "N/A",
                    "SizeGB": size_gb,
                    "Partitions": particiones,
                    "FirmwareRevision": safe_str(
                        getattr(drive, "FirmwareRevision", "N/A")
                    ),
                    "BytesPerSector": safe_str(getattr(drive, "BytesPerSector", "512")),
                    "Status": status,
                    "IsSSD": "SSD" in model.upper()
                    or "SOLID STATE" in media_type.upper(),
                    "DeviceID": safe_str(getattr(drive, "DeviceID", "N/A")),
                }

                dispositivos["Discos"][disk_type].append(disco_info)

            return dispositivos

        except ImportError:
            return {}
        except Exception as e:
            print("Error al obtener los dispositivos: {}".format(str(e)))
            return {}

    def resource_path(self, relative_path):
        """Obtiene la ruta correcta tanto en desarrollo como en ejecutable"""
        try:
            # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def get_historial_dispositivos(self):
        resultado = []
        campos_necesarios = {
            "Description",
            "Device Type",
            "Connected",
            "Serial Number",
            "Registry Time 2",
        }

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".txt", delete=False
        ) as temp_file:
            temp_path = temp_file.name

        try:
            # Obtener la ruta correcta al ejecutable
            ruta_exe = self.resource_path("utils/usbdeview/USBDeview.exe")

            # Configurar flags para evitar errores de handle
            creationflags = 0x08000000  # CREATE_NO_WINDOW para Python 3.4

            # Ejecutar USBDeview
            proceso = subprocess.Popen(
                [ruta_exe, "/stext", temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=creationflags,  # Evita el error de handle
            )
            proceso.wait()  # Esperar a que termine

            # Verificar si el proceso se ejecutó correctamente
            if proceso.returncode != 0:
                print("Error al ejecutar USBDeview: {}".format(str(proceso.returncode)))
                return None

            # Leer el archivo con codificación latin-1 (para evitar errores)
            with open(temp_path, "r", encoding="latin-1") as archivo:
                dispositivo_actual = {}

                for linea in archivo:
                    linea = linea.strip()

                    # Inicio de un nuevo dispositivo
                    if linea.startswith("==="):
                        if dispositivo_actual:
                            # Verificar si NO es un dispositivo HID antes de agregar
                            if (
                                dispositivo_actual.get("Device Type")
                                != "HID (Human Interface Device)"
                            ):
                                resultado.append(dispositivo_actual)
                            dispositivo_actual = {}
                        continue

                    # Extraer clave-valor
                    if ":" in linea:
                        clave, valor = [parte.strip() for parte in linea.split(":", 1)]
                        if clave in campos_necesarios:
                            dispositivo_actual[clave] = valor

                # Asegurarse de agregar el último dispositivo (si no es HID)
                if (
                    dispositivo_actual
                    and dispositivo_actual.get("Device Type")
                    != "HID (Human Interface Device)"
                ):
                    resultado.append(dispositivo_actual)

        except Exception as e:
            print("Error al ejecutar USBDeview: {}".format(str(e)))
            return None

        finally:
            # Eliminar archivo temporal
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print("Error al eliminar el archivo temporal: {}".format(str(e)))

        return resultado

    def version_windows(self):
        version_win = platform.release()

        if version_win == "10" or version_win == "11":
            return "Windows 10 o 11"
        elif version_win <= "7" or "XP":
            return "Seven o XP"
        else:
            return "Otro"

    def get_estado_usb(self):
        """Lista los puertos USB y su estado"""
        if self.version_windows() == "Windows 10 o 11":
            kaspersky_path = AntivirusInfoWindows.get_kaspersky_path()
            if kaspersky_path:
                try:
                    # Comprobamos el estado de diferentes componentes de Kaspersky
                    stat_output = subprocess.check_output(
                        [os.path.join(kaspersky_path, "avp.com"), "STATUS"],
                        stderr=subprocess.STDOUT,
                    ).decode("latin1")
                    for line in stat_output.splitlines():
                        if "DeviceControl " in line:
                            estado = line.split()[-1].strip()
                            if estado == "running":
                                return "Control Dispositivos: Running"
                            else:
                                return "Control Dispositivos: Dissable"
                except subprocess.CalledProcessError as e:
                    print(
                        "Error al ejecutar el comando avp.com STATUS: {}".format(str(e))
                    )
            return ""
        elif self.version_windows() == "Seven o XP":
            nombres_procesos = [
                "gfi_languard_agent.exe",
                "GFI.EPS.Agent.exe",
                "gfi_fw_engine.exe",
            ]
            nombres_servicios = ["GFI LanGuard Agent", "GFI EPS Agent"]

            try:
                # Verificar procesos en ejecucion
                proceso_activo = False
                tasklist_output = subprocess.check_output(
                    ["tasklist"], shell=True
                ).decode("latin-1")
                for nombre in nombres_procesos:
                    if re.search(nombre, tasklist_output, re.IGNORECASE):
                        print("Proceso activo: {}".format(nombre))
                        proceso_activo = True

                # Verificar servicios (sc query)
                servicio_activo = False
                for servicio in nombres_servicios:
                    sc_output = subprocess.check_output(
                        'sc query "{}"'.format(servicio), shell=True
                    ).decode("latin-1")
                    if "RUNNING" in sc_output.upper():
                        print("Servicio activo: {}".format(servicio))
                        servicio_activo = True

            except Exception as e:
                print("Error al verificar los procesos y servicios: {}".format(str(e)))

            if proceso_activo or servicio_activo:
                return "Activo"
            return "Inactivo"
