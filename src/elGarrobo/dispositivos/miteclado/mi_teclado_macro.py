# https://python-evdev.readthedocs.io/en/latest/
import threading
import time

from evdev import InputDevice, categorize, ecodes
from evdev.eventio import EvdevError

from elGarrobo.dispositivos import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)

# TODO  Hacer con clase threading


class MiTecladoMacro(dispositivo):
    """Clase de Teclado Macro para Linux."""

    modulo = "teclado"
    tipo = "teclado"
    archivoConfiguracion = "teclados.md"

    teclado: InputDevice | None = None
    "Objeto del teclado"

    def __init__(self, dataConfiguracion: dict) -> None:
        """Inicializando Dispositivo de teclado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """
        super().__init__(dataConfiguracion)
        self.nombre = dataConfiguracion.get("nombre", "Teclado")

        self.conectado = False
        self.Activo = True
        self.esperaReconectar = 5

    def conectar(self):
        """Conecta con un teclado para escuchas botones presionados."""
        self.procesoTeclado = threading.Thread(name="teclados-" + self.nombre, target=self.HiloTeclado)
        self.procesoTeclado.start()

    def HiloTeclado(self):
        """Hilo del estado del Teclado."""
        while self.Activo:
            if self.conectado:
                try:
                    for event in self.teclado.read_loop():
                        if not self.Activo:
                            break
                        if event.type == ecodes.EV_KEY:
                            key = categorize(event)

                            match key.keystate:
                                case key.key_down:
                                    self.buscarAccion(key.keycode, self.estadoTecla.PRESIONADA)
                                case key.key_hold:
                                    self.buscarAccion(key.keycode, self.estadoTecla.MANTENIDA)
                                case key.key_up:
                                    self.buscarAccion(key.keycode, self.estadoTecla.LIBERADA)
                except OSError as error:
                    if error.errno == 9:
                        # Se ha cerrado el dispositivo: salir del bucle de forma controlada.
                        logger.info(f"Teclado[{self.nombre}] - Dispositivo cerrado, saliendo del hilo.")
                        break
                    else:
                        self.conectado = False
                        logger.exception("Error en Colección del Teclado")

                except Exception as error:
                    self.conectado = False
                    logger.exception("Error en Colección del Teclado")
                    # logger.info(f"Teclado[Desconectado] {self.nombre} Error[{error.errno}]")
            else:
                try:
                    logger.info(f"Teclado[Conectándose] {self.nombre} - {self.dispositivo}")
                    self.teclado: InputDevice = InputDevice(self.dispositivo)
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
        self.conectado = False
        time.sleep(0.5)
        if self.teclado is not None:
            try:
                if hasattr(self, "teclado") and self.teclado:
                    self.teclado.ungrab()
                    self.teclado.close()
            except Exception as e:
                logger.error(f"Error al cerrar el dispositivo: {e}")
