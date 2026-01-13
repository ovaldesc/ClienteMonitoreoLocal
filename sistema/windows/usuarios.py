# sistema/windows/usuario.py
import subprocess
from getpass import getuser
import win32net


class UsuarioWindows:

    def get_usuario_activo(self):
        return getuser()

    def get_usuarios(self):
        """Obtiene la lista de usuarios ACTIVOS (habilitados) del sistema Windows."""

        # === Método 1: win32net (mejor opción, filtra por UF_ACCOUNTDISABLE) ===
        try:
            import win32netcon

            usuarios = []
            resume = 0
            while True:
                data, total, resume = win32net.NetUserEnum(
                    None,
                    3,  # nivel 3 incluye 'flags'
                    win32netcon.FILTER_NORMAL_ACCOUNT,
                )
                for user in data:
                    if not (user["flags"] & win32netcon.UF_ACCOUNTDISABLE):
                        usuarios.append(user["name"])
                if not resume:
                    break
            if usuarios:
                return usuarios
        except Exception as e:
            print("Error con win32net: {}".format(str(e)))

        # === Método 2: wmic (filtra explícitamente por disabled=0) ===
        try:
            output = subprocess.check_output(
                'wmic useraccount where "disabled=0" get name',
                universal_newlines=True,
                shell=True,
            )
            lines = output.split("\n")
            usuarios = [
                line.strip()
                for line in lines
                if line.strip() and line.strip() != "Name"
            ]
            if usuarios:
                return usuarios
        except Exception as e:
            print("Error con wmic: {}".format(str(e)))

        # === Todos fallaron ===
        return ["Error: No se pudieron obtener los usuarios del sistema"]

    def get_admins(self):
        """Obtiene los usuarios administradores en Windows."""
        try:
            for group_name in ["Administradores", "Administrators"]:
                try:
                    data = win32net.NetLocalGroupGetMembers(None, group_name, 1)
                    raw_admins = [user["name"] for user in data[0]]
                    return [
                        admin
                        for admin in raw_admins
                        if admin.lower() not in ["administrador", "administrator"]
                    ]
                except Exception as e:
                    continue
            return ["Error: No se encontró el grupo de administradores"]
        except Exception as e:
            return ["Error al obtener admins: {0}".format(e)]
