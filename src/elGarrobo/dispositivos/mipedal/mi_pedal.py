# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Transport.Transport import TransportError

from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


class MiPedal(dispositivo):

    nombre = "Pedal StreamDeck"
    modulo = "pedal"
    tipo = "pedal"
    descripcion = "Pedal Elgato StreamDeck"
    compatibles = ["Stream Deck Pedal"]

    archivoConfiguracion = "pedal.md"
    deck: DeviceManager = None
    idDeck: int = -1
    cantidad: int = 3
    "Cantidad de pedales"
    desfaceTeclas: int = 0
    "Página actual: el primer pedal hace la acción desfaceTeclas + 1"
    paginaGlobal: bool = False
    "Solo cambia de página con acciones que indiquen este dispositivo, no con las globales"

    def __init__(self, dataConfiguracion: dict) -> None:
        """Inicializando Dispositivo de teclado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """
        super().__init__(dataConfiguracion)
        self.nombre = dataConfiguracion.get("nombre", "pedal")

        self.id = dataConfiguracion.get("id", "")
        self.conectado: bool = False

    def conectar(self) -> None:
        streamdecks = DeviceManager().enumerate()

        listaIdUsados = dispositivo.listaIndexUsados

        for idActual, deck in enumerate(streamdecks):

            if deck.DECK_TYPE not in self.compatibles:
                continue

            idProbar = True
            for idUsado in listaIdUsados:
                if idActual == idUsado:
                    idProbar = False

            if idProbar:
                try:
                    self.deck = deck
                    self.deck.open()
                    self.deck.reset()
                    if self.deck.get_serial_number() == self.dispositivo and self.deck.deck_type() == "Stream Deck Pedal":
                        self.conectado = True
                        self.cantidad = self.deck.key_count()
                        self.deck.set_key_callback(self.actualizarBoton)
                        self.idDeck = idActual
                        dispositivo.agregarIndexUsado(self.idDeck)
                        return
                    else:
                        self.deck.close()
                except TransportError as error:
                    self.conectado = False
                    self.deck = None
                    logger.exception(f"Error 1 {error}")
                    logger.error(f"Error 1 {error}")
                except Exception as error:
                    self.conectado = False
                    self.deck = None
                    logger.exception(f"Error 2 {error}")
                    logger.error(f"Error 2 {error}")

    def actualizarBoton(self, Deck, Key: int, Estado: bool):
        if Estado:
            self.buscarAccion(Key + 1 + self.desfaceTeclas, self.estadoTecla.PRESIONADA)
        else:
            self.buscarAccion(Key + 1 + self.desfaceTeclas, self.estadoTecla.LIBERADA)

    def desconectar(self):
        if self.conectado:
            logger.info(f"Pedal[Desconectando] - {self.nombre}")
            self.conectado = False
            self.deck.reset()
            self.deck.close()

    def distribucionBotones(self) -> tuple[int, int]:
        return (1, self.cantidad)

    def cargarAccionesFolder(self, folder: str = "/", recargar: bool = False):
        super().cargarAccionesFolder(folder, recargar)
        if self.recargar:
            self.desfaceTeclas = 0

    def siguientePagina(self) -> None:
        """Pasa a los siguientes pedales, si hay acciones más adelante"""
        teclas = [int(acción.get("key")) for acción in self.listaAcciones or [] if str(acción.get("key")).isdigit()]
        if self.desfaceTeclas + self.cantidad >= max(teclas, default=0):
            logger.info(f"No se puede adelantar pagina {self.nombre}")
            return
        self.desfaceTeclas += self.cantidad
        self.avisarCambioPagina()

    def anteriorPagina(self) -> None:
        if self.desfaceTeclas - self.cantidad < 0:
            logger.info(f"No se puede regresar pagina {self.nombre}")
            return
        self.desfaceTeclas -= self.cantidad
        self.avisarCambioPagina()

    def avisarCambioPagina(self) -> None:
        logger.info(f"Pedal[Pagina] {self.nombre} teclas {self.desfaceTeclas + 1}-{self.desfaceTeclas + self.cantidad}")
        if self.funcionActualizarPestaña is not None:
            self.funcionActualizarPestaña(self)
