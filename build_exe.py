import os
import sys
import subprocess

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CLIENTE = os.path.join(BASE_DIR, "main.py")

PYTHON_EXEC = sys.executable


def add_data_arg(folder):
    src = os.path.join(BASE_DIR, folder)
    return src + ";" + folder


add_data_args = [
    "--add-data",
    add_data_arg("core"),
    "--add-data",
    add_data_arg("services"),
    "--add-data",
    add_data_arg("sistema"),
    "--add-data",
    add_data_arg("utils"),
]

common_args = [
    PYTHON_EXEC,
    "-m",
    "PyInstaller",
    "--onefile",
    "--clean",
    "--noconfirm",
    "--hidden-import",
    "requests",
    "--hidden-import",
    "win32net",
    "--hidden-import",
    "win32netcon",
    "--hidden-import",
    "pywintypes",
    "--hidden-import",
    "wmi",
    "--hidden-import",
    "ctypes",
    "--name",
    "ClienteMonitoreo",
]

cliente_cmd = common_args + add_data_args + [CLIENTE]

subprocess.call(cliente_cmd)

print("Ejecutables generados en la carpeta dist/")
