# https://python-evdev.readthedocs.io/en/latest/
import threading
import time

from evdev import InputDevice, categorize, ecodes
from evdev.eventio import EvdevError

from elGarrobo.dispositivos.dispositivoBase import dispositivoBase
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)

# TODO  Hacer con clase threading


class MiTecladoMacro(dispositivoBase):
    """Clase de Teclado Macro para Linux."""

    def __init__(self, nombre: str, dispositivo: str, archivo: str, Evento, folderPerfil: str) -> None:
        """Inicializando Dispositivo de teclado

        Args:
            nombre (str): Nombre del dispositivo
            dispositivo (str): Ruta del dispositivo
            archivo (str): Ruta del archivo de configuración
            Evento (callable): Función a llamar en caso de evento
            folderPerfil (str): Carpeta del perfil

        """
        self.Dispositivo = dispositivo
        self.File = archivo
        self.Evento = Evento
        self.Conectado = False
        self.Activo = True
        self.EsperaReconectar = 5
        super().__init__(nombre, dispositivo, archivo, folderPerfil)

    # def run(self):
    #     """Dibuja un frame de cada gif y espera a siguiente frame."""
    #     while True:
    #         with self.lock:
    #             print("hola :D")

    def conectar(self):
        """Conecta con un teclado para escuchas botones presionados."""
        self.HiloTeclado = threading.Thread(name="teclados-" + self.nombre, target=self.HiloRaton)
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
                            data.update({"nombre": self.nombre, "key": key.keycode})

                            match key.keystate:
                                case key.key_down:
                                    data.update({"estado": "presionado"})
                                case key.key_hold:
                                    data.update({"estado": "mantener"})
                                case key.key_up:
                                    data.update({"estado": "soltar"})
                            self.Evento(data)
                except Exception as error:
                    self.Conectado = False
                    logger.info(f"Teclado[Desconectado] {self.nombre} Error[{error.errno}]")
            else:
                try:
                    logger.info(f"Teclado[Conectándose] {self.nombre}")
                    self.Teclado = InputDevice(self.Dispositivo)
                    self.Teclado.grab()
                    self.Conectado = True
                    logger.info(f"Teclado[Conectado] {self.nombre}")
                except Exception as error:
                    logger.warning(f"Teclado[Error] {self.nombre} Re-Intensando en {self.EsperaReconectar} Error {error.errno}")
                    if self.EsperaReconectar < 60:
                        self.EsperaReconectar += 5
                    time.sleep(self.EsperaReconectar)
                    self.Conectado = False

    def desconectar(self):
        logger.info(f"Teclado[Desconectando] {self.nombre}")
        self.Activo = False
        self.Teclado.ungrab()
        self.Teclado.close()
        # self.HiloTeclado.join()
