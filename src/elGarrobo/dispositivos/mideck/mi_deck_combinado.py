from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging

from .mi_streamdeck import MiStreamDeck
from .mi_streamdeck_plus import MiStreamDeckPlus

logger = ConfigurarLogging(__name__)


class MiDeckCombinado(dispositivo):

    modulo = "deck_combinado"
    tipo = "deck_combinado"
    archivoConfiguracion = "deck_combinado.md"
    "Archivo de configuración del dispositivo"
    listaDeck: list[MiStreamDeck] = list()
    "Lista de Dispositivos StreamDeck a combinar"
    imagenesBase: dict = None
    "Imagen que se una por defecto"
    desface: int = 0
    """Cuantas botones esta adelante del inicio
    
    ejemplo:
        desface es 10, el segundo botón haría la acción 12 
    """
    cantidadBotones: int = 0
    "Cantidad de botones en StreamDeck Combinado"
    cantidadDial: int = 0
    "Cantidad de Dial en StreamDeck Combinado"

    archivoFuente: str = None
    "fuente para texto de botones"
    fps: int = 60
    "fotogramas por segundo para gif"

    def __init__(self, dataConfiguracion: dict) -> None:
        """Inicializando Dispositivo de MiDeckCombinado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """

        super().__init__(dataConfiguracion)
        self.listaDeck = list()
        self.nombre = dataConfiguracion.get("nombre", "DeckCombinado")
        self.archivoFuente = dataConfiguracion.get("fuente", "")
        self.imagenesBase = dataConfiguracion.get("imagen_base", "")
        self.fps = dataConfiguracion.get("fps", 20)
        dataStreamDecks: dict = dataConfiguracion.get("streamDecks")
        dataStreamDecksPlus: dict = dataConfiguracion.get("streamDecksPlus")

        if dataStreamDecks is not None:
            for deckActual in dataStreamDecks:
                deckTemporal: MiStreamDeck = MiStreamDeck(deckActual)
                deckTemporal.archivoFuente = self.archivoFuente
                deckTemporal.imagenesBase = self.imagenesBase
                deckTemporal.fps = self.fps
                self.listaDeck.append(deckTemporal)

        if dataStreamDecksPlus is not None:
            for deckActualPlus in dataStreamDecksPlus:
                deckTemporal: MiStreamDeckPlus = MiStreamDeckPlus(deckActualPlus)
                deckTemporal.archivoFuente = self.archivoFuente
                deckTemporal.imagenesBase = self.imagenesBase
                deckTemporal.fps = self.fps
                self.listaDeck.append(deckTemporal)

    def conectar(self) -> None:
        """Conecta todos los dispositivos los dispositivos"""

        baseActual: int = 1
        baseDial: int = 1

        for deckActual in self.listaDeck:
            deckActual.baseTeclas = baseActual
            deckActual.conectar()
            baseActual += deckActual.cantidadBotones
            if hasattr(baseActual, "cantidadDial"):
                baseActual.baseDial = baseDial
                baseDial += baseActual.cantidadDial

        self.cantidadBotones = baseActual - 1
        self.cantidadDial = baseDial - 1

    def cargarAccionesFolder(self, folder: str = "/", recargar: bool = False):
        """Busca y carga acciones en un folder, si existen

        Args:
            folder (str): folder a buscar acciones
            recargar (boo, optional):

        """

        if not self.activado:
            return

        # folderAnterior = self.folderActual

        super().cargarAccionesFolder(folder, recargar)

        if not self.recargar:
            return

        for deckActual in self.listaDeck:
            deckActual.listaAcciones = self.listaAcciones
            deckActual.folderActual = self.folderActual
            deckActual.desfaceTeclas = 0

        # if self.folderActual != folderAnterior or recargar:
        #     self.limpiarIconos()
        #     self.actualizarIconos()

    def configurarFuncionAccion(self, funcionAccion: callable):
        """Prepara la la funciona para ejecutar acciones"""

        super().configurarFuncionAccion(funcionAccion)

        for deckActual in self.listaDeck:
            deckActual.configurarFuncionAccion(funcionAccion)

    def limpiarIconos(self):
        "Limpia los iconos de los StreamDeck"

        for deck in self.listaDeck:
            deck.limpiarIconos()

    def actualizarIconos(self):
        "pone los iconos en base de la lista de acciones cargadas"

        for deck in self.listaDeck:
            deck.actualizarIconos()

    def siguientePagina(self):
        """Cambia la pagina los StreamDeck Combinados"""

        if not self.listaAcciones:
            logger.warning(f"No hay acciones para cambiar pagina en {self.nombre}")
            return

        def buscarKeyNumero(accionActual: dict):
            try:
                key = int(accionActual["key"])
            except ValueError:
                return None
            return key

        ultimaAccion: int = max(self.listaAcciones, key=buscarKeyNumero).get("key")

        for deck in self.listaDeck:
            if deck.desfaceTeclas + self.cantidadBotones + 1 > ultimaAccion:
                logger.info(f"No se puede adelantar pagina {self.nombre}")
                return

        for deck in self.listaDeck:
            deck.desfaceTeclas += self.cantidadBotones
        self.recargar = True

    def anteriorPagina(self):
        """Regresa una pagina los StreamDeck Combinados"""

        if not self.listaAcciones:
            logger.warning(f"No hay acciones para cambiar pagina en {self.nombre}")
            return

        for deck in self.listaDeck:
            if deck.desfaceTeclas - self.cantidadBotones < 0:
                logger.info(f"No se puede regresar pagina {self.nombre}")
                return

        for deck in self.listaDeck:
            deck.desfaceTeclas -= self.cantidadBotones

        self.recargar = True

    def desconectar(self):

        for deck in self.listaDeck:
            deck.desconectar()

    def actualizar(self):

        if self.recargar:

            # self.limpiarIconos()
            self.actualizarIconos()

        super().actualizar()
