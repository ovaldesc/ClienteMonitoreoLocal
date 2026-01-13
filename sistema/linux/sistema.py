# sistema/linux/sistema.py
import socket
import datetime
import platform
import subprocess
import re


class SistemaLinux:
    def obtener_nombre_pc(self):
        return socket.gethostname()

    def get_ip(self):
        try:
            result = subprocess.check_output(
                ["ip", "addr", "show"], universal_newlines=True, timeout=5
            )
            for line in result.split("\n"):
                if "inet " in line and "127.0.0.1" not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip = parts[1].split("/")[0]
                        if ip and not ip.startswith("127."):
                            return ip
        except:
            return "127.0.0.1"

    def get_version_so(self):
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=")[1].strip().strip('"')
        except:
            try:
                result = subprocess.check_output(
                    ["lsb_release", "-d"], universal_newlines=True
                )
                return result.split(":")[1].strip()
            except:
                try:
                    return "{} {}".format(platform.system(), platform.release())
                except:
                    return "Linux - Información no disponible"

    def get_fecha_ejecucion(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_installed_apps(self):
        """
        Obtiene SOLO las aplicaciones instaladas explícitamente por el usuario.
        Usa el historial de apt y filtra agresivamente paquetes del sistema base.
        """
        apps_list = []
        user_installed_packages = set()

        # Intentar obtener paquetes instalados explícitamente desde el historial de apt
        try:
            history_files = [
                "/var/log/apt/history.log",
                "/var/log/dpkg.log",
            ]

            for history_file in history_files:
                try:
                    with open(
                        history_file, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        content = f.read()
                        # Buscar líneas que indican instalación explícita
                        # Formato: "install package1 package2" o "Commandline: apt install package"
                        install_pattern = (
                            r"(?:install|Commandline:.*install)\s+([^\n]+)"
                        )
                        matches = re.findall(install_pattern, content, re.IGNORECASE)

                        for match in matches:
                            # Extraer nombres de paquetes (sin versión)
                            packages = re.findall(r"(\S+?)(?::\S+)?(?:\s|$)", match)
                            for pkg in packages:
                                # Limpiar nombre del paquete
                                pkg = pkg.strip().rstrip(":")
                                if pkg and not pkg.startswith("-") and pkg != "install":
                                    user_installed_packages.add(pkg)
                except (IOError, PermissionError):
                    continue
        except Exception:
            pass

        # Si no encontramos en el historial, usar apt-mark showmanual como fallback
        if not user_installed_packages:
            try:
                manual_packages = subprocess.check_output(
                    ["apt-mark", "showmanual"],
                    universal_newlines=True,
                    timeout=30,
                    stderr=subprocess.DEVNULL,
                ).splitlines()
                user_installed_packages = {
                    pkg.strip() for pkg in manual_packages if pkg.strip()
                }
            except:
                return []

        # Prefijos y sufijos de paquetes del sistema a excluir (muy agresivo)
        excluded_prefixes = [
            "lib",
            "python3-",
            "perl",
            "ruby",
            "gir1.2-",
            "fonts-",
            "linux-",
            "xserver-",
            "x11-",
            "mesa-",
            "libreoffice-l10n-",
            "libreoffice-help-",
            "accountsservice",
            "acl",
            "acpi-",
            "adduser",
            "alsa-",
            "amd64-microcode",
            "anacron",
            "apache2-",
            "apg",
            "apport",
            "appstream",
            "apt",
            "apt-",
            "base-files",
            "bash",
            "bc",
            "bind9-",
            "binutils",
            "bzip2",
            "ca-certificates",
            "coreutils",
            "cpio",
            "cron",
            "curl",
            "dash",
            "dbus",
            "debconf",
            "debianutils",
            "diffutils",
            "dnsutils",
            "dpkg",
            "e2fsprogs",
            "findutils",
            "gawk",
            "gcc-",
            "gdb",
            "gdm3",
            "git",
            "gnome-",
            "grep",
            "gzip",
            "hdparm",
            "hostname",
            "ifupdown",
            "init",
            "initramfs-",
            "initscripts",
            "insserv",
            "iproute2",
            "iptables",
            "iputils-",
            "isc-dhcp-",
            "kbd",
            "keyboard-configuration",
            "kmod",
            "less",
            "libc6",
            "libgcc1",
            "libstdc++",
            "locale",
            "locales",
            "login",
            "logrotate",
            "lsb-",
            "makedev",
            "man-db",
            "manpages",
            "mawk",
            "mime-support",
            "mount",
            "ncurses-",
            "net-tools",
            "netbase",
            "netcat-",
            "network-manager",
            "nfs-",
            "openssh-",
            "openssl",
            "passwd",
            "patch",
            "pciutils",
            "perl-base",
            "procps",
            "psmisc",
            "python3-minimal",
            "readline-",
            "resolvconf",
            "rsync",
            "sed",
            "sensible-utils",
            "shadow",
            "shared-mime-info",
            "sudo",
            "sysvinit-",
            "sysv-rc",
            "tar",
            "tasksel",
            "tcpdump",
            "telnet",
            "time",
            "tzdata",
            "ubuntu-",
            "udev",
            "ufw",
            "unzip",
            "update-",
            "upstart",
            "usbutils",
            "util-linux",
            "vim-",
            "wget",
            "which",
            "xauth",
            "xkb-data",
            "xml-core",
            "xz-utils",
            "zlib1g",
            "ubuntu-minimal",
            "ubuntu-standard",
        ]

        # Secciones del sistema a excluir
        excluded_sections = [
            "libs",
            "libdevel",
            "oldlibs",
            "admin",
            "base",
            "devel",
            "utils",
            "cli-mono",
            "comm",
            "database",
            "debug",
            "doc",
            "editors",
            "electronics",
            "embedded",
            "fonts",
            "gnu-r",
            "gnustep",
            "golang",
            "hamradio",
            "haskell",
            "httpd",
            "interpreters",
            "introspection",
            "java",
            "javascript",
            "kernel",
            "lisp",
            "localization",
            "mail",
            "math",
            "metapackages",
            "misc",
            "net",
            "news",
            "ocaml",
            "otherosfs",
            "perl",
            "php",
            "python",
            "ruby",
            "science",
            "shells",
            "sound",
            "tasks",
            "tex",
            "text",
            "vcs",
            "video",
            "web",
            "x11",
            "zope",
            "oldlibs",
        ]

        # Prioridades del sistema a excluir (solo incluir "optional" y "extra")
        excluded_priorities = ["required", "important", "standard", "buildd"]

        # Procesar cada paquete instalado por el usuario
        for package in user_installed_packages:
            package = package.strip()
            if not package:
                continue

            # Filtrar por prefijos excluidos
            if any(package.startswith(prefix) for prefix in excluded_prefixes):
                continue

            # Filtrar paquetes que terminan en sufijos de desarrollo/sistema
            if any(
                package.endswith(suffix)
                for suffix in ["-dev", "-dbg", "-common", "-data", "-bin", "-utils"]
            ):
                continue

            try:
                # Obtener información completa del paquete
                info = subprocess.check_output(
                    [
                        "dpkg-query",
                        "-W",
                        "-f=${Package}\t${Version}\t${Section}\t${Priority}\n",
                        package,
                    ],
                    universal_newlines=True,
                    timeout=5,
                    stderr=subprocess.DEVNULL,
                ).strip()

                if info:
                    parts = info.split("\t")
                    if len(parts) >= 2:
                        package_name = parts[0]
                        version = parts[1]
                        section = parts[2] if len(parts) > 2 else ""
                        priority = parts[3] if len(parts) > 3 else ""

                        # Filtrar por sección del sistema
                        if section:
                            section_lower = section.lower()
                            if any(
                                exc_sec in section_lower
                                for exc_sec in excluded_sections
                            ):
                                continue

                        # Filtrar por prioridad (solo incluir optional y extra)
                        if priority:
                            priority_lower = priority.lower()
                            if priority_lower in excluded_priorities:
                                continue

                        # Incluir solo si pasa todos los filtros
                        apps_list.append((package_name, version))

            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue

        # Ordenar y devolver
        return sorted(apps_list, key=lambda x: x[0].lower())
