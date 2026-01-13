import os
import sys
import subprocess

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CLIENTE = os.path.join(BASE_DIR, "main.py")


def add_data_arg(folder):
    src = os.path.join(BASE_DIR, folder)
    return "{}:{}".format(src, folder)


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
    "pyinstaller",
    "--onefile",
    "--clean",
    "--noconfirm",
    "--console",
    "--hidden-import",
    "requests",
    *add_data_args,
]

subprocess.run(common_args + [CLIENTE], check=True)

print("Ejecutables generados en la carpeta dist/")
