# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Transport.Transport import TransportError

from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


class MiPedal(dispositivo):

    modulo = "pedal"
    tipo = "pedal"
    compatibles = ["Stream Deck Pedal"]

    archivoConfiguracion = "pedal.md"
    deck: DeviceManager = None
    idDeck: int = -1

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
                    self.Conectado = False
                    self.deck = None
                    logger.exception(f"Error 1 {error}")
                    logger.error(f"Error 1 {error}")
                except Exception as error:
                    self.Conectado = False
                    self.deck = None
                    logger.exception(f"Error 2 {error}")
                    logger.error(f"Error 2 {error}")

    def actualizarBoton(self, Deck, Key: int, Estado: bool):
        if Estado:
            self.buscarAccion(str(Key + 1), self.estadoTecla.PRESIONADA)
        else:
            self.buscarAccion(str(Key + 1), self.estadoTecla.LIBERADA)

    def desconectar(self):
        if self.conectado:
            logger.info(f"Pedal[Desconectando] - {self.nombre}")
            self.Conectado = False
            self.deck.reset()
            self.deck.close()
