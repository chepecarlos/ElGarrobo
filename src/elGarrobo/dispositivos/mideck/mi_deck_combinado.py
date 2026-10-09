from typing import Optional, Union

from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging

from .mi_streamdeck import MiStreamDeck
from .mi_streamdeck_plus import MiStreamDeckPlus

logger = ConfigurarLogging(__name__)


class MiDeckCombinado(dispositivo):

    nombre = "StreamDeck"
    modulo = "deck_combinado"
    tipo = "deck_combinado"
    descripcion = "Elgato StreamDeck (incluye StreamDeck+)"
    archivoConfiguracion = "deck_combinado.md"
    "Archivo de configuración del dispositivo"
    listaDeck: list[Union[MiStreamDeck, MiStreamDeckPlus]] = list()
    "Lista de Dispositivos StreamDeck a combinar"
    imagenesBase: Optional[dict[str, str]] = None
    "Imagen que se una por defecto"
    desfase: int = 0
    """Cuantas botones esta adelante del inicio

    ejemplo:
        desfase es 10, el segundo botón haría la acción 12 
    """
    cantidadBotones: int = 0
    "Cantidad de botones en StreamDeck Combinado"
    cantidadDial: int = 0
    "Cantidad de Dial en StreamDeck Combinado"

    archivoFuente: Optional[str] = None
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
        self.archivoFuente: str = dataConfiguracion.get("fuente", "")
        self.imagenesBase: dict[str, str] = dataConfiguracion.get("imagen_base", dict())
        self.fps = dataConfiguracion.get("fps", 20)
        dataStreamDecks: dict = dataConfiguracion.get("streamDecks")
        dataStreamDecksPlus: dict = dataConfiguracion.get("streamDecksPlus")

        if dataStreamDecks is not None:
            for deckActual in dataStreamDecks:
                deckTemporal = MiStreamDeck(deckActual)
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

        super().cargarAccionesFolder(folder, recargar)

    def accionesCargadas(self) -> None:
        """Pasa las acciones y el folder a cada StreamDeck antes de avisar a la GUI"""
        for deckActual in self.listaDeck:
            deckActual.listaAcciones = self.listaAcciones
            deckActual.folderActual = self.folderActual
            deckActual.desfaseTeclas = 0
        super().accionesCargadas()

    def configurarFuncionAccion(self, funcionAccion: callable):
        """Prepara la la funciona para ejecutar acciones"""

        super().configurarFuncionAccion(funcionAccion)

        for deckActual in self.listaDeck:
            deckActual.configurarFuncionAccion(funcionAccion)

    def limpiarIconos(self):
        "Limpia los iconos de los StreamDeck"

        for deck in self.listaDeck:
            deck.limpiarIconos()

    def gruposBotones(self) -> list:
        """Las teclas de cada StreamDeck que lo forman, cada uno con su tamaño y rotación"""
        return [grupo for deck in self.listaDeck for grupo in deck.gruposBotones()]

    def tamañoBoton(self) -> tuple[int, int]:
        """Tamaño de las teclas del primer StreamDeck"""
        if self.listaDeck:
            return self.listaDeck[0].tamañoBoton()
        return super().tamañoBoton()

    def actualizarIconos(self):
        "pone los iconos en base de la lista de acciones cargadas"

        for deck in self.listaDeck:
            deck.actualizarIconos()

    def _desfase(self) -> int:
        """Desfase de la página actual, todos los StreamDeck avanzan juntos"""
        return self.listaDeck[0].desfaseTeclas if self.listaDeck else 0

    def paginaActual(self) -> int:
        if self.cantidadBotones <= 0:
            return 1
        return self._desfase() // self.cantidadBotones + 1

    def puedeSiguientePagina(self, editando: bool = False) -> bool:
        """Hay acciones después de la página actual; editando permite una página vacía extra para agregar acciones"""
        extra = self.cantidadBotones if editando else 0
        return self.cantidadBotones > 0 and self._desfase() + self.cantidadBotones < self.ultimaTecla() + extra

    def puedeAnteriorPagina(self) -> bool:
        return self.cantidadBotones > 0 and self._desfase() >= self.cantidadBotones

    def siguientePagina(self, editando: bool = False):
        """Cambia la pagina los StreamDeck Combinados"""

        if not self.puedeSiguientePagina(editando):
            logger.info(f"No se puede adelantar pagina {self.nombre}")
            return

        for deck in self.listaDeck:
            deck.desfaseTeclas += self.cantidadBotones
        self.recargar = True
        self.avisarGui()

    def anteriorPagina(self):
        """Regresa una pagina los StreamDeck Combinados"""

        if not self.puedeAnteriorPagina():
            logger.info(f"No se puede regresar pagina {self.nombre}")
            return

        for deck in self.listaDeck:
            deck.desfaseTeclas -= self.cantidadBotones

        self.recargar = True
        self.avisarGui()

    def desconectar(self):

        for deck in self.listaDeck:
            deck.desconectar()

    def actualizar(self):

        if self.recargar:

            for deck in self.listaDeck:
                deck.actualizar()

            # self.limpiarIconos()
            self.actualizarIconos()

        super().actualizar()
