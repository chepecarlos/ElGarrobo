# https://python-evdev.readthedocs.io/en/latest/
import threading
import time

from evdev import InputDevice, categorize, ecodes
from evdev.eventio import EvdevError


from Extra.CargarData import ExisteArchivo, CargarValores

import MiLibrerias

logger = MiLibrerias.ConfigurarLogging(__name__)


# TODO  Hacer con clase threading
class MiTecladoMacro(threading.Thread):
    """Clase de Teclado Macro para Linux."""

    def __init__(self, Nombre, Dispisitivo, File, FuncionEvento):
        """ ."""
        self.Nombre = Nombre
        self.Dispisitivo = Dispisitivo
        self.File = File
        self.FuncionEvento = FuncionEvento
        self.Conectado = False
        self.EsperaReconectar = 5
        super(MiTecladoMacro, self).__init__()

    def run(self):
        """Dibuja un frame de cada gif y espera a siquiente frame."""
        while True:
            with self.lock:
                print("hola :D")

    def Conectar(self):
        """Conecta con un teclado para escuchas botones precionados."""
        print(f"Activando Hilo de Teclado {self.Nombre}")
        self.HiloTeclado = threading.Thread(name="teclados-" + self.Nombre, target=self.HiloRaton, daemon=True)
        self.HiloTeclado.start()

    def ActualizarTeclas(self, Archivo):
        if ExisteArchivo(Archivo + "/" + self.File, True):
            logger.info(f"Cargando Archivo {self.File}")
            self.TeclasActuales = CargarValores(Archivo + "/" + self.File, True)

    def HiloRaton(self):
        """Hilo del estado del Teclado."""
        while True:    
            if self.Conectado:
                try:
                    for event in self.Teclado.read_loop():
                        if event.type == ecodes.EV_KEY:
                            key = categorize(event)
                            data = dict()
                            if key.keystate == key.key_down:
                                data = {"nombre": self.Nombre,
                                        "key": key.keycode,
                                        "estado": True}
                            else:
                                data = {"nombre": self.Nombre,
                                        "key": key.keycode,
                                        "estado": False}
                            self.FuncionEvento(data)
                except Exception as error:
                    self.Conectado = False
                    print(f"Se desconecto Teclado {self.Nombre} Error: {error.errno}")
            else:
                try:
                    logger.info(f"Intentando conectarse: {self.Nombre} - {self.Dispisitivo}")
                    self.Teclado = InputDevice(self.Dispisitivo)
                    self.Teclado.grab()
                    self.Conectado = True
                    logger.info(f"Conectando Teclado: {self.Nombre} - {self.Dispisitivo}")
                except Exception as error:
                    logger.warning(f"No se puedo conectar con teclado {self.Nombre} Error {error.errno}")
                    logger.info(f"Ïntentado Reconecar con Teclado {self.Nombre} en {self.EsperaReconectar} Segundos")
                    time.sleep(self.EsperaReconectar)
                    self.Conectado = False
