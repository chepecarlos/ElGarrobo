# https://python-evdev.readthedocs.io/en/latest/
import threading
import logging

from evdev import InputDevice, categorize, ecodes


# from Extra.Acciones import Accion
from Extra.CargarData import ExisteArchivo, CargarValores

from libreria.FuncionesLogging import ConfigurarLogging

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class MiTecladoMacro:
    def __init__(self, Nombre, Dispisitivo, File, FuncionEvento):
        self.Nombre = Nombre
        self.Dispisitivo = Dispisitivo
        self.File = File
        self.FuncionEvento = FuncionEvento

    def Conectar(self):
        try:
            self.Teclado = InputDevice(self.Dispisitivo)
            self.Teclado.grab()
            self.HiloTeclado = threading.Thread(name="teclados", target=self.HiloRaton, args=(self.Teclado, self.Nombre,), daemon=True)
            self.HiloTeclado.start()
            logger.info(f"Conectando: {self.Nombre} - {self.Dispisitivo}")
        except Exception:
            logger.warning(f"Error con Teclado {self.Nombre}")
            return False
        return True

    def ActualizarTeclas(self, Archivo):
        if ExisteArchivo(Archivo + "/" + self.File, True):
            logger.info(f"Cargando Archivo {self.File}")
            self.TeclasActuales = CargarValores(Archivo + "/" + self.File, True)

    def HiloRaton(self, Teclado, Nombre):
        '''Hila del teclado del Teclado'''
        for event in Teclado.read_loop():
            if event.type == ecodes.EV_KEY:
                key = categorize(event)
                data = dict()
                if key.keystate == key.key_down:
                    data = {"nombre": Nombre,
                            "key": key.keycode,
                            "estado": True}
                else:
                    data = {"nombre": Nombre,
                            "key": key.keycode,
                            "estado": False}
                self.FuncionEvento(data)
