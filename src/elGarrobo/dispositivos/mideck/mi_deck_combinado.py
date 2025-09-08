from elGarrobo.dispositivos.dispositivoBase import dispositivoBase
from elGarrobo.miLibrerias import ConfigurarLogging

from .mi_streamdeck import MiStreamDeck

logger = ConfigurarLogging(__name__)


class MiDeckCombinado(dispositivoBase):

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

    archivoFuente: str = None
    "fuente para texto de botones"

    def __init__(self, dataConfiguracion: dict):
        """Inicializando Dispositivo de MiDeckCombinado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """

        self.nombre = dataConfiguracion.get("nombre", "DeckCombinado")
        self.archivo = dataConfiguracion.get("archivo", "")
        self.archivoFuente = dataConfiguracion.get("fuente", "")
        self.imagenesBase = dataConfiguracion.get("imagen_base", "")
        dataStreamDecks: dict = dataConfiguracion.get("streamDecks")

        for deckActual in dataStreamDecks:
            deckTemporal: MiStreamDeck = MiStreamDeck(deckActual)
            deckTemporal.archivoFuente = self.archivoFuente
            deckTemporal.imagenesBase = self.imagenesBase
            self.listaDeck.append(deckTemporal)

    def conectar(self) -> None:
        """Conecta todos los dispositivos los dispositivos"""

        baseActual: int = 1

        for deckActual in self.listaDeck:
            deckActual.baseTeclas = baseActual
            deckActual.conectar()
            baseActual += deckActual.cantidadBotones

        self.cantidadBotones = baseActual - 1

    def cargarAccionesFolder(self, folder: str = "/", recargar: bool = False):
        """Busca y carga acciones en un folder, si existen

        Args:
            folder (str): folder a buscar acciones
            recargar (boo, optional):

        """

        if not self.activado:
            return

        folderAnterior = self.folderActual

        super().cargarAccionesFolder(folder, recargar)

        for deckActual in self.listaDeck:
            deckActual.listaAcciones = self.listaAcciones
            deckActual.folderActual = self.folderActual

        if self.folderActual != folderAnterior or recargar:
            self.limpiarIconos()
            self.actualizarIconos()

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

        ultimaAccion = max(self.listaAcciones, key=lambda x: int(x["key"])).get("key")

        for deck in self.listaDeck:
            if deck.desfaceTeclas + self.cantidadBotones > ultimaAccion:
                logger.info(f"No se puede adelantar pagina {self.nombre}")
                return

        for deck in self.listaDeck:
            deck.desfaceTeclas += self.cantidadBotones

        self.limpiarIconos()
        self.actualizarIconos()

    def anteriorPagina(self):
        """Regresa una pagina los StreamDeck Combinados"""

        for deck in self.listaDeck:
            if deck.desfaceTeclas - self.cantidadBotones < 0:
                logger.info(f"No se puede regresar pagina {self.nombre}")
                return

        for deck in self.listaDeck:
            deck.desfaceTeclas -= self.cantidadBotones

        self.limpiarIconos()
        self.actualizarIconos()
