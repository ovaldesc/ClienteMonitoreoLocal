# sistemas/windows/seguridad.py

import winreg
import subprocess
import wmi


class SeguridadWindows:
    def is_escritorio_remoto_habilitado(self):
        try:
            reg_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Terminal Server",
                0,
                winreg.KEY_READ,
            )
            value, _ = winreg.QueryValueEx(reg_key, "fDenyTSConnections")
            return "Habilitado" if value == 0 else "Deshabilitado"
        except Exception as e:
            return "Error: {e}".format(e=e)

    def get_parches_seguridad(self):
        """Obtiene los parches de seguridad instalados en Windows."""
        patches = []

        # Método 1: Usar WMI
        try:
            import wmi

            c = wmi.WMI()
            patches_wmi = c.Win32_QuickFixEngineering()
            patches = [
                "{}, {}, {}".format(p.HotFixID, p.Description, p.InstalledOn)
                for p in patches_wmi
            ]
            if patches:
                return patches
        except Exception as e:
            print("Error con wmi: {}".format(str(e)))

        # Método 2: Usar PowerShell como alternativa
        try:
            ps_command = "Get-HotFix | Select-Object HotFixID, Description, InstalledOn | ForEach-Object { '{0}, {1}, {2}' -f $_.HotFixID, $_.Description, $_.InstalledOn }"
            output = subprocess.check_output(
                ["powershell", "-Command", ps_command],
                universal_newlines=True,
                shell=True,
            )
            patches = [line.strip() for line in output.split("\n") if line.strip()]
            if patches:
                return patches
        except Exception as e:
            print("Error con powershell: {}".format(str(e)))

        # Método 3: Usar wmic como último recurso
        try:
            output = subprocess.check_output(
                [
                    "wmic",
                    "qfe",
                    "get",
                    "HotFixID,Description,InstalledOn",
                    "/format:csv",
                ],
                universal_newlines=True,
                shell=True,
            )
            lines = output.split("\n")
            patches = []
            for line in lines[1:]:  # Saltar la primera línea (header)
                if line.strip() and "," in line:
                    parts = line.split(",")
                    if len(parts) >= 4:
                        patches.append(
                            "{}, {}, {}".format(parts[1], parts[2], parts[3])
                        )
            if patches:
                return patches
        except Exception as e:
            print("Error con wmic: {}".format(str(e)))

        # Si todos los métodos fallan, devolver error
        return ["Error: No se pudieron obtener los parches de seguridad"]

    def esta_unido_kms(self):
        try:
            resultado = subprocess.check_output(
                ["tasklist"], shell=True, universal_newlines=True
            )
            return "kms-service.exe" in resultado.lower()
        except Exception as e:
            return False
