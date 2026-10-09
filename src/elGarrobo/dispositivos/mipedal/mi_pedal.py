# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Transport.Transport import TransportError

from elGarrobo.dispositivos.dispositivo import dispositivo, grupoBotones
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
    desfaseTeclas: int = 0
    "Página actual: el primer pedal hace la acción desfaseTeclas + 1"
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
            self.buscarAccion(Key + 1 + self.desfaseTeclas, self.estadoTecla.PRESIONADA)
        else:
            self.buscarAccion(Key + 1 + self.desfaseTeclas, self.estadoTecla.LIBERADA)

    def desconectar(self):
        if self.conectado:
            logger.info(f"Pedal[Desconectando] - {self.nombre}")
            self.conectado = False
            self.deck.reset()
            self.deck.close()

    def gruposBotones(self) -> list[grupoBotones]:
        return [grupoBotones(self.nombre, 1, self.cantidad, self.desfaseTeclas + 1, self)]

    def accionesCargadas(self) -> None:
        self.desfaseTeclas = 0
        super().accionesCargadas()

    def paginaActual(self) -> int:
        return self.desfaseTeclas // self.cantidad + 1

    def puedeSiguientePagina(self, editando: bool = False) -> bool:
        """Hay acciones después de la página actual; editando permite una página vacía extra para agregar acciones"""
        extra = self.cantidad if editando else 0
        return self.desfaseTeclas + self.cantidad < self.ultimaTecla() + extra

    def puedeAnteriorPagina(self) -> bool:
        return self.desfaseTeclas >= self.cantidad

    def siguientePagina(self, editando: bool = False) -> None:
        """Pasa a los siguientes pedales, si hay acciones más adelante"""
        if not self.puedeSiguientePagina(editando):
            logger.info(f"No se puede adelantar pagina {self.nombre}")
            return
        self.desfaseTeclas += self.cantidad
        self.avisarCambioPagina()

    def anteriorPagina(self) -> None:
        if not self.puedeAnteriorPagina():
            logger.info(f"No se puede regresar pagina {self.nombre}")
            return
        self.desfaseTeclas -= self.cantidad
        self.avisarCambioPagina()

    def avisarCambioPagina(self) -> None:
        logger.info(f"Pedal[Pagina] {self.nombre} teclas {self.desfaseTeclas + 1}-{self.desfaseTeclas + self.cantidad}")
        self.avisarGui()
