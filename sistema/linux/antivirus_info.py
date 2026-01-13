#antivirus_info.py de linux
import subprocess


class AntivirusInfoLinux:

    def __init__(self):
        self.command = "segavcli info --show"
        self.field_mappings = {
            "Versión": "Version",
            "Autorizado a": "Licencia",
            "Fecha de expiración": "Fecha de expiración",
            "Deshabilitada": "Protección permanente",
            "Habilitada": "Protección permanente",
            "Fecha de la actualización": "Fecha de la actualización",
        }

    def get_segurmatica_info(self):

        try:

            result = subprocess.check_output(
                ["which", "segavcli"], stderr=subprocess.DEVNULL, timeout=5
            )

            result = subprocess.check_output(
                self.command,
                shell=True,
                universal_newlines=True,
                timeout=10,
                stderr=subprocess.DEVNULL,
            )

            segurmatica_info = {}
            self._process_output(result, segurmatica_info)
            return segurmatica_info

        except subprocess.CalledProcessError:
            return {
                "mensaje": "Antivirus Segurmatica no está instalado en el dispositivo"
            }
        except subprocess.TimeoutExpired:
            return {"mensaje": "Antivirus Segurmatica expiro el tiempo de respuesta"}
        except Exception:
            return {"mensaje": "Antivirus Segurmatica excepcion no verificada"}

    def _process_output(self, output, info):

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            # Procesamiento de campos mapeados
            for pattern, field in self.field_mappings.items():
                if pattern in line:
                    info[field] = line.split(": ")[-1].strip()
                    break

            # Procesamiento especial para resultados de búsqueda
            if "Revisados" in line:
                info["Objetos revisados"] = line.split(": ")[-1].strip()
            elif (
                "Fecha" in line
                and "Revisados" not in line
                and "actualización" not in line
            ):
                info["Resultado de la última búsqueda"] = line.split(": ")[-1].strip()
