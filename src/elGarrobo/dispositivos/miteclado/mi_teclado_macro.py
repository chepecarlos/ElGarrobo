# https://python-evdev.readthedocs.io/en/latest/
import threading
import time

from evdev import InputDevice, categorize, ecodes
from evdev.eventio import EvdevError

from elGarrobo.miLibrerias import ConfigurarLogging
from elGarrobo.miLibrerias import UnirPath

logger = ConfigurarLogging(__name__)

# TODO  Hacer con clase threading


class MiTecladoMacro():
    """Clase de Teclado Macro para Linux."""

    def __init__(self, Nombre, Dispisitivo, File, Evento):
        """ ."""
        self.Nombre = Nombre
        self.Dispisitivo = Dispisitivo
        self.File = File
        self.Evento = Evento
        self.Conectado = False
        self.Activo = True
        self.EsperaReconectar = 5
        # super(MiTecladoMacro, self).__init__()

    # def run(self):
    #     """Dibuja un frame de cada gif y espera a siquiente frame."""
    #     while True:
    #         with self.lock:
    #             print("hola :D")

    def Conectar(self):
        """Conecta con un teclado para escuchas botones precionados."""
        self.HiloTeclado = threading.Thread(
            name="teclados-" + self.Nombre, target=self.HiloRaton)
        self.HiloTeclado.start()

    def HiloRaton(self):
        """Hilo del estado del Teclado."""
        while self.Activo:
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
                            self.Evento(data)
                except Exception as error:
                    self.Conectado = False
                    logger.info(
                        f"Teclado[Desconectado] {self.Nombre} Error[{error.errno}]")
            else:
                try:
                    logger.info(f"Teclado[Conectándose] {self.Nombre}")
                    self.Teclado = InputDevice(self.Dispisitivo)
                    self.Teclado.grab()
                    self.Conectado = True
                    logger.info(f"Teclado[Conectado] {self.Nombre}")
                except Exception as error:
                    logger.warning(f"Teclado[Error] {self.Nombre} Re-Intensando en {self.EsperaReconectar} Error {error.errno}")
                    if self.EsperaReconectar < 60:
                        self.EsperaReconectar += 5
                    time.sleep(self.EsperaReconectar)
                    self.Conectado = False

    def Desconectar(self):
        logger.info(f"Teclado[Desconectando] {self.Nombre}")
        self.Activo = False
        self.Teclado.ungrab()
        self.Teclado.close()
        # self.HiloTeclado.join()
