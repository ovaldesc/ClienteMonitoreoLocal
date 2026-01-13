# utils/log_redirect.py
import sys
import datetime
import os
from .config_manager import ConfigManager

class Logger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.terminal = sys.stdout
        self.log = open(log_file, "a", encoding="utf-8")
        # Atributos requeridos por Python para file-like objects
        self.encoding = "utf-8"
        self.errors = "strict"  # o "replace", "ignore"
        self.line_buffering = False
        self.write_through = False

    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()
        if message.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted = message if message.endswith("\n") else message + "\n"
            self.log.write("[{}] {}".format(timestamp, formatted))
            self.log.flush()

    def flush(self):
        self.terminal.flush()
        if hasattr(self.log, "flush"):
            self.log.flush()

    def close(self):
        if hasattr(self.log, "close"):
            self.log.close()

def start_logging(log_file_name="CSI.log"):
    config = ConfigManager()
    log_path = os.path.join(config.config_dir, log_file_name)
    try:
        logger = Logger(log_path)
        sys.stdout = logger
        sys.stderr = logger
        return logger
    except Exception as e:
        print("Error al iniciar logging: {}".format(str(e)))
        return None

def stop_logging():
    try:
        if isinstance(sys.stdout, Logger):
            sys.stdout.close()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    except Exception:
        pass