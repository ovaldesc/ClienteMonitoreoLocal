# utils/utiles.py

import threading
import platform


class Tarea(threading.Thread):
    def __init__(self, target, name, args=(), kwargs={}):
        super(Tarea, self).__init__()
        self.target = target
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.exception = None

    def run(self):
        try:
            # Solo inicializar COM en Windows
            if platform.system() == "Windows":
                import pythoncom

                pythoncom.CoInitialize()

            self.result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.exception = e
        finally:
            # Solo desinicializar COM en Windows
            if platform.system() == "Windows":
                try:
                    import pythoncom

                    pythoncom.CoUninitialize()
                except:
                    pass


class EjecutorParalelo:
    def __init__(self):
        self.tareas = {}  # Eliminamos el type hint

    def agregar_tarea(self, nombre, target, args=(), kwargs={}):
        self.tareas[nombre] = Tarea(
            target=target, name=nombre, args=args, kwargs=kwargs
        )

    def ejecutar(self):
        for tarea in self.tareas.values():
            tarea.start()

        for tarea in self.tareas.values():
            tarea.join()

        resultados = {}
        for nombre, tarea in self.tareas.items():
            if tarea.exception:
                raise RuntimeError(
                    "Error en tarea '{}': {}".format(nombre, tarea.exception)
                )
            resultados[nombre] = tarea.result

        return resultados
