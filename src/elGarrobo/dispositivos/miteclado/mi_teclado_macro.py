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

    modulo = "teclado"
    tipo = "teclado"
    archivoConfiguracion = "teclados.md"

    teclado: InputDevice
    "Objeto del teclado"

    def __init__(self, dataConfiguracion: dict) -> None:
        """Inicializando Dispositivo de teclado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """
        self.nombre = dataConfiguracion.get("nombre", "Teclado")
        self.dispositivo = dataConfiguracion.get("dispositivo", "")
        self.archivo = dataConfiguracion.get("archivo", "")
        self.activado = dataConfiguracion.get("activado", True)
        self.conectado = False
        self.Activo = True
        self.esperaReconectar = 5

        super().__init__()

    def conectar(self):
        """Conecta con un teclado para escuchas botones presionados."""
        self.HiloTeclado = threading.Thread(name="teclados-" + self.nombre, target=self.HiloRaton)
        self.HiloTeclado.start()

    def HiloRaton(self):
        """Hilo del estado del Teclado."""
        while self.Activo:
            if self.conectado:
                try:
                    for event in self.teclado.read_loop():
                        if event.type == ecodes.EV_KEY:
                            key = categorize(event)

                            match key.keystate:
                                case key.key_down:
                                    self.buscarAccion(key.keycode, self.estadoTecla.PRESIONADA)
                                case key.key_hold:
                                    self.buscarAccion(key.keycode, self.estadoTecla.MANTENIDA)
                                case key.key_up:
                                    self.buscarAccion(key.keycode, self.estadoTecla.LIBERADA)

                except Exception as error:
                    self.conectado = False
                    logger.exception("Error en Coneccion del Teclado")
                    logger.info(f"Teclado[Desconectado] {self.nombre} Error[{error.errno}]")
            else:
                try:
                    logger.info(f"Teclado[Conectándose] {self.nombre} - {self.dispositivo}")
                    self.teclado = InputDevice(self.dispositivo)
                    self.teclado.grab()
                    self.conectado = True
                    logger.info(f"Teclado[Conectado] {self.nombre}")
                except Exception as error:
                    logger.exception("An error occurred during division.")
                    logger.warning(f"Teclado[Error] {self.nombre} Re-Intensando en {self.esperaReconectar} Error {error.errno}")
                    if self.esperaReconectar < 60:
                        self.esperaReconectar += 5
                    time.sleep(self.esperaReconectar)
                    self.conectado = False

    def desconectar(self):
        logger.info(f"Teclado[Desconectando] {self.nombre}")
        self.Activo = False
        self.teclado.ungrab()
        self.teclado.close()
        # self.HiloTeclado.join()
