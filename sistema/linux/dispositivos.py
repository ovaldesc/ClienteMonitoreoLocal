# sistema/linux/dispositivos.py

import subprocess
import re
import os


class DispositivoLinux:

    def get_dispositivos_conectados(self):
        """
        Obtiene dispositivos conectados en Linux con múltiples métodos alternativos
        """
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

        # =================== CÁMARAS - MÚLTIPLES MÉTODOS ===================
        dispositivos["Cámaras"] = self._obtener_camaras()

        # =================== IMPRESORAS - MÚLTIPLES MÉTODOS ===================
        dispositivos["Impresoras Activas"] = self._obtener_impresoras()

        # =================== ESCÁNERES - MÚLTIPLES MÉTODOS ===================
        dispositivos["Escáneres"] = self._obtener_escaneres()

        # =================== DISCOS - MÚLTIPLES MÉTODOS ===================
        dispositivos["Discos"] = self._obtener_discos()

        return dispositivos

    def _obtener_camaras(self):
        """Múltiples métodos para detectar cámaras"""
        camaras = []

        # Método 1: v4l2-ctl (primario)
        try:
            subprocess.check_call(
                ["which", "v4l2-ctl"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            output = subprocess.check_output(
                ["v4l2-ctl", "--list-devices"], stderr=subprocess.STDOUT, timeout=10
            ).decode()

            current_device = ""
            for line in output.split("\n"):
                line = line.strip()
                if line and not line.startswith("/dev/"):
                    # Es el nombre del dispositivo
                    current_device = line
                elif line.startswith("/dev/video"):
                    # Es un dispositivo de video
                    if current_device:
                        camara_info = "{} ({})".format(current_device, line)
                    else:
                        camara_info = line
                    if camara_info not in camaras:
                        camaras.append(camara_info)
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            pass

        # Método 2: Buscar dispositivos /dev/video*
        if not camaras:
            try:
                for device in os.listdir("/dev"):
                    if device.startswith("video"):
                        camaras.append("/dev/{}".format(device))
            except OSError:
                pass

        # Método 3: Usar lsusb para encontrar dispositivos de video
        if not camaras:
            try:
                output = subprocess.check_output(
                    ["lsusb"], stderr=subprocess.STDOUT, timeout=5
                ).decode()
                for line in output.split("\n"):
                    line_lower = line.lower()
                    if any(
                        keyword in line_lower
                        for keyword in ["camera", "webcam", "video", "imaging"]
                    ):
                        camaras.append("USB: {}".format(line.strip()))
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        # Método 4: Verificar módulos de cámara cargados
        if not camaras:
            try:
                output = subprocess.check_output(
                    ["lsmod"], stderr=subprocess.STDOUT, timeout=5
                ).decode()
                cam_modules = []
                for line in output.split("\n"):
                    if any(
                        keyword in line.lower()
                        for keyword in ["uvc", "video", "camera", "webcam"]
                    ):
                        parts = line.split()
                        if parts and parts[0] not in ["Module", "uvcvideo"]:
                            cam_modules.append(parts[0])

                if cam_modules:
                    camaras.extend(
                        ["Módulo: {}".format(mod) for mod in cam_modules[:3]]
                    )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        return camaras if camaras else ["No se detectaron cámaras"]

    def _obtener_impresoras(self):
        """Múltiples métodos para detectar impresoras"""
        impresoras = []

        # Método 1: lpstat (CUPS)
        try:
            subprocess.check_call(
                ["which", "lpstat"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            output = subprocess.check_output(
                ["lpstat", "-p"], stderr=subprocess.STDOUT, timeout=10
            ).decode()

            for line in output.split("\n"):
                line_lower = line.lower()
                if "printer" in line_lower and "is" in line_lower:
                    parts = line.split()
                    if len(parts) >= 2:
                        printer_name = parts[1]
                        # Verificar estado
                        try:
                            status_output = subprocess.check_output(
                                ["lpstat", "-p", printer_name],
                                stderr=subprocess.STDOUT,
                                timeout=5,
                            ).decode()
                            if "enabled" in status_output.lower():
                                impresoras.append(
                                    "{} (CUPS - Habilitada)".format(printer_name)
                                )
                            else:
                                impresoras.append(
                                    "{} (CUPS - Deshabilitada)".format(printer_name)
                                )
                        except (
                            subprocess.CalledProcessError,
                            subprocess.TimeoutExpired,
                        ):
                            impresoras.append(
                                "{} (CUPS - Estado desconocido)".format(printer_name)
                            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            pass

        # Método 2: Verificar servicio CUPS
        if not impresoras:
            try:
                cups_status = (
                    subprocess.check_output(
                        ["systemctl", "is-active", "cups"],
                        stderr=subprocess.DEVNULL,
                        timeout=5,
                    )
                    .decode()
                    .strip()
                )
                if cups_status == "active":
                    impresoras.append(
                        "Servicio CUPS activo (sin impresoras configuradas)"
                    )
                else:
                    impresoras.append("Servicio CUPS inactivo")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        # Método 3: Impresoras USB via lsusb
        if not impresoras:
            try:
                output = subprocess.check_output(
                    ["lsusb"], stderr=subprocess.STDOUT, timeout=5
                ).decode()
                for line in output.split("\n"):
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in ["printer", "print"]):
                        impresoras.append("USB: {}".format(line.strip()))
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        return impresoras if impresoras else ["No se detectaron impresoras"]

    def _obtener_escaneres(self):
        """Múltiples métodos para detectar escáneres - CORREGIDO"""
        escaneres = []

        # Método 1: scanimage (SANE) - MEJORADO
        try:
            subprocess.check_call(
                ["which", "scanimage"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            output = subprocess.check_output(
                ["scanimage", "-L"], stderr=subprocess.STDOUT, timeout=10
            ).decode()

            # Filtrar solo líneas que contengan dispositivos reales
            for line in output.split("\n"):
                line_clean = line.strip()
                if "device" in line_clean.lower() and (
                    "`" in line_clean or "is a" in line_clean.lower()
                ):
                    # Limpiar la información
                    if "is a" in line_clean.lower():
                        device_info = line_clean.split("is a")[0].strip()
                    else:
                        device_info = line_clean

                    # Excluir líneas de error
                    if not any(
                        error in line_clean.lower()
                        for error in ["no devices", "error", "failed"]
                    ):
                        escaneres.append(device_info)

        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            pass

        # Método 2: sane-find-scanner - MEJORADO
        if not escaneres:
            try:
                subprocess.check_call(
                    ["which", "sane-find-scanner"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                output = subprocess.check_output(
                    ["sane-find-scanner"], stderr=subprocess.STDOUT, timeout=10
                ).decode()

                # Filtrar solo líneas con dispositivos encontrados
                for line in output.split("\n"):
                    line_clean = line.strip()
                    # Buscar líneas que mencionen dispositivos específicos
                    if any(
                        keyword in line_clean.lower()
                        for keyword in ["found", "scanner", "/dev/", "usb:"]
                    ):
                        # Excluir líneas de error o instrucciones
                        if not any(
                            exclude in line_clean.lower()
                            for exclude in [
                                "if you expected",
                                "make sure",
                                "adjust access",
                                "no ",
                                "could not",
                                "not found",
                            ]
                        ):
                            if line_clean and len(line_clean) > 10:
                                escaneres.append(line_clean)

            except (
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ):
                pass

        # Método 3: Escáneres USB via lsusb
        if not escaneres:
            try:
                output = subprocess.check_output(
                    ["lsusb"], stderr=subprocess.STDOUT, timeout=5
                ).decode()
                for line in output.split("\n"):
                    line_clean = line.strip()
                    if any(
                        keyword in line_clean.lower() for keyword in ["scanner", "scan"]
                    ):
                        escaneres.append("USB: {}".format(line_clean))
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        # Filtrar resultados finales
        escaneres_limpios = []
        for escaner in escaneres:
            # Excluir líneas que sean mensajes de error o instrucciones
            if not any(
                exclude in escaner.lower()
                for exclude in [
                    "if you expected",
                    "make sure that",
                    "adjust access",
                    "could not",
                    "no scsi",
                    "no usb",
                    "not found",
                    "permission denied",
                ]
            ):
                if escaner.strip() and len(escaner.strip()) > 5:
                    escaneres_limpios.append(escaner.strip())

        return (
            escaneres_limpios if escaneres_limpios else ["No se detectaron escáneres"]
        )

    def _obtener_discos(self):
        """Múltiples métodos para obtener información de discos"""
        discos = {
            "Internos": [],
            "Externos_USB": [],
            "Removibles": [],
            "Opticos": [],
            "Desconocidos": [],
        }

        # Método 1: lsblk (primario)
        try:
            output = subprocess.check_output(
                ["lsblk", "-o", "NAME,TYPE,SIZE,MODEL,MOUNTPOINT,TRAN"],
                stderr=subprocess.STDOUT,
                timeout=10,
            ).decode()
            self._procesar_lsblk(output, discos)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        # Método 2: df para información de montaje
        try:
            output = subprocess.check_output(
                ["df", "-h"], stderr=subprocess.STDOUT, timeout=5
            ).decode()
            self._completar_info_montaje(output, discos)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        # Método 3: /proc/partitions como respaldo
        if not any(discos.values()):
            try:
                self._procesar_proc_partitions(discos)
            except:
                pass

        return discos

    def _procesar_lsblk(self, output, discos):
        """Procesa salida de lsblk"""
        lines = output.split("\n")
        if len(lines) < 2:
            return

        for line in lines[1:]:  # Saltar cabecera
            if not line.strip():
                continue

            parts = re.split(r"\s+", line.strip(), maxsplit=5)
            if len(parts) < 3:
                continue

            name, dtype, size = parts[0], parts[1], parts[2]
            model = parts[3] if len(parts) > 3 else "Desconocido"
            mountpoint = parts[4] if len(parts) > 4 else ""
            transport = parts[5] if len(parts) > 5 else ""

            # Solo procesar discos (no particiones)
            if dtype != "disk":
                continue

            disk_type = self._clasificar_disco(dtype, transport, name)

            disco_info = {
                "Nombre": name,
                "Modelo": model if model != "Desconocido" else "Sin modelo",
                "Tamaño": size,
                "PuntoMontaje": mountpoint,
                "Transporte": transport,
                "Dispositivo": "/dev/{}".format(name),
            }

            discos[disk_type].append(disco_info)

    def _procesar_proc_partitions(self, discos):
        """Procesa /proc/partitions para información básica de discos"""
        try:
            with open("/proc/partitions", "r", encoding="utf-8") as f:
                for line in f.readlines()[2:]:  # Saltar cabeceras
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        name = parts[3]
                        # Solo discos, no particiones
                        if any(
                            name.startswith(prefix)
                            for prefix in ["sd", "hd", "nvme", "vd"]
                        ):
                            size_blocks = int(parts[2])
                            size_gb = (size_blocks * 1024) / (1024**3)  # Convertir a GB

                            disco_info = {
                                "Nombre": name,
                                "Tamaño": "{:.1f} GB".format(size_gb),
                                "Dispositivo": "/dev/{}".format(name),
                            }

                            discos["Desconocidos"].append(disco_info)
        except (IOError, ValueError):
            pass

    def _completar_info_montaje(self, df_output, discos):
        """Completa información de puntos de montaje usando df"""
        for line in df_output.split("\n")[1:]:  # Saltar cabecera
            if not line.strip():
                continue

            parts = re.split(r"\s+", line.strip())
            if len(parts) >= 6:
                dispositivo = parts[0]
                punto_montaje = parts[5]

                # Buscar y actualizar información de montaje en todos los discos
                for tipo in discos:
                    for disco in discos[tipo]:
                        if disco["Dispositivo"] == dispositivo:
                            disco["PuntoMontaje"] = punto_montaje
                            break

    def _clasificar_disco(self, dtype, transport, name):
        """Clasifica el tipo de disco"""
        if transport == "usb":
            return "Externos_USB"
        elif "mmcblk" in name or (
            "sd" in name and any(c in name for c in ["a", "b", "c"])
        ):
            return "Removibles"
        elif dtype == "rom":
            return "Opticos"
        else:
            return "Internos"

    def get_historial_dispositivos(self):
        """
        Obtiene historial de dispositivos USB con múltiples métodos
        """
        historial = []

        # Método 1: journalctl (primario)
        try:
            output = subprocess.check_output(
                [
                    "journalctl",
                    "--no-pager",
                    "-k",
                    "--since",
                    "7 days ago",
                    "-o",
                    "short",
                ],
                stderr=subprocess.STDOUT,
                timeout=10,
            ).decode()

            usb_events = []
            for line in output.split("\n"):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ["usb", "hid"]):
                    # Filtrar eventos relevantes
                    if any(
                        event in line_lower
                        for event in ["new device", "disconnect", "product:"]
                    ):
                        usb_events.append(line.strip())

            historial = [
                {"Evento": event} for event in usb_events[:10]
            ]  # Limitar a 10 eventos

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass

        # Método 2: dmesg (alternativo)
        if not historial:
            try:
                output = subprocess.check_output(
                    ["dmesg"], stderr=subprocess.STDOUT, timeout=5
                ).decode()
                usb_events = [
                    line for line in output.split("\n") if "usb" in line.lower()
                ]
                historial = [{"Evento": event[:100]} for event in usb_events[:10]]
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        return (
            historial if historial else [{"Info": "No se pudo obtener historial USB"}]
        )

    def get_estado_usb(self):
        """
        Verifica el estado de los puertos USB
        """
        try:
            # Verificar dispositivos USB conectados
            usb_devices = subprocess.check_output(
                ["lsusb"], stderr=subprocess.STDOUT, timeout=5
            ).decode()
            device_count = len(
                [line for line in usb_devices.split("\n") if line.strip()]
            )

            # Verificar módulos USB
            lsmod_output = subprocess.check_output(
                ["lsmod"], stderr=subprocess.STDOUT, timeout=5
            ).decode()
            usb_modules = [
                line.split()[0]
                for line in lsmod_output.split("\n")
                if any(
                    mod in line
                    for mod in ["usb_storage", "uhci", "ehci", "xhci", "ohci"]
                )
            ]

            status = "USB: {} dispositivos detectados".format(device_count)
            if usb_modules:
                status += ", {} módulos cargados".format(len(usb_modules))

            return status

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return "USB: Estado no disponible"
