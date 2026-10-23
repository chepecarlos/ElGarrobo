# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Transport.Transport import TransportError

from elGarrobo.dispositivos.dispositivo import dispositivo, grupoBotones
from elGarrobo.dispositivos.mideck.mi_streamdeck import listarStreamDecks
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


class MiPedal(dispositivo):

    nombre = "Pedal StreamDeck"
    modulo = "pedal"
    tipo = "pedal"
    descripcion = "Pedal Elgato StreamDeck"
    compatibles = ["Stream Deck Pedal"]

    archivoConfiguracion = "pedal.md"
    icono = "touch_app"
    deck: DeviceManager = None
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

    @staticmethod
    def listarDisponibles() -> list[tuple[str, str]]:
        """(serial, modelo) de los pedales conectados"""
        return listarStreamDecks(MiPedal.compatibles)

    def conectar(self) -> None:
        # ponytail: se prueban todos los compatibles por serial, como MiStreamDeck; los que ya usa otro
        # fallan al abrir y se saltan
        for deck in DeviceManager().enumerate():
            if deck.DECK_TYPE not in self.compatibles:
                continue
            try:
                deck.open()
                if deck.get_serial_number() != self.dispositivo:
                    deck.close()
                    continue
                # reset después del serial, si no reinicia otro pedal
                deck.reset()
                self.deck = deck
                self.conectado = True
                self.cantidad = deck.key_count()
                deck.set_key_callback(self.actualizarBoton)
                return
            except TransportError:
                continue
            except Exception as error:
                self.conectado = False
                self.deck = None
                logger.exception(f"Pedal[Error] {self.nombre}: {error}")
        logger.warning(f"Pedal[No encontrado] {self.nombre}[{self.dispositivo}]")

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
