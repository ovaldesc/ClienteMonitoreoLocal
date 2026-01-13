# sistema/linux/seguridad.py
import subprocess


class SeguridadLinux:
    def is_escritorio_remoto_habilitado(self):
        try:
            result = subprocess.check_output(["ss", "-tuln"], universal_newlines=True)
            return "Habilitado" if "3389" in result else "Deshabilitado"
        except Exception as e:
            return "Error: {}".format(e)

    def get_parches_seguridad(self):
        try:
            result = subprocess.check_output(
                ["dpkg-query", "-l"], universal_newlines=True
            )
            lines = result.splitlines()
            return [line for line in lines if "security" in line.lower()]
        except Exception as e:
            return ["Error: {}".format(e)]

    def esta_unido_kms(self):
        return False
