# sistema/linux/usuario.py
from getpass import getuser


class UsuarioLinux:

    def get_usuario_activo(self):
        return getuser()

    def get_usuarios(self):
        """Obtiene la lista de usuarios del sistema Linux."""
        try:
            with open("/etc/passwd", "r") as f:
                usuarios = [
                    line.split(":")[0]
                    for line in f
                    if not line.startswith("#") and self._es_usuario_habilitado(line)
                ]
            return usuarios
        except Exception as e:
            return ["Error al obtener usuarios: {}".format(e)]

    def get_admins(self):
        """Obtiene los usuarios administradores en Linux."""
        try:
            with open("/etc/group", "r") as f:
                admins = []
                for line in f:
                    if line.startswith("sudo:") or line.startswith("wheel:"):
                        usuarios = line.strip().split(":")[3].split(",")
                        admins.extend(usuarios)
                return admins
        except Exception as e:
            return ["Error al obtener admins: {}".format(e)]

    def _es_usuario_habilitado(self, line):
        shell = line.strip().split(":")[-1]
        return shell not in ["/sbin/nologin", "/bin/false", "/usr/sbin/nologin"]
