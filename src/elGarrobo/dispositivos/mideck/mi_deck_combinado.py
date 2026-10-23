from typing import Optional, Union

from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor

from .mi_streamdeck import MiStreamDeck, listarStreamDecks
from .mi_streamdeck_plus import MiStreamDeckPlus

logger = ConfigurarLogging(__name__)


class MiDeckCombinado(dispositivo):

    nombre = "StreamDeck"
    modulo = "deck_combinado"
    tipo = "deck_combinado"
    descripcion = "Elgato StreamDeck (incluye StreamDeck+)"
    archivoConfiguracion = "deck_combinado.md"
    icono = "grid_view"
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

    propiedadesAparato = [
        propiedadAccion("Brillo", "brillo", [int], defecto=70, descripcion="Brillo normal de 0 a 100"),
        propiedadAccion(
            "Minutos para reposo",
            "minutos_reposo",
            [int],
            defecto=0,
            descripcion="Minutos sin uso para bajar el brillo, 0 lo desactiva",
        ),
        propiedadAccion(
            "Brillo en reposo",
            "brillo_reposo",
            [int],
            defecto=0,
            descripcion="De 0 a 100; con 0 se apaga y la primera tecla solo despierta",
        ),
    ]

    @staticmethod
    def notaAparato(data: dict) -> str:
        """Explica el reposo configurado, sobre todo que con brillo_reposo 0 la primera tecla solo despierta"""
        minutos = data.get("minutos_reposo", 0)
        if not minutos:
            return "Reposo desactivado: pon los minutos para bajar el brillo cuando no se usa y cuidar las pantallas"
        brillo = data.get("brillo_reposo", 0)
        if brillo:
            return f"Reposo: tras {minutos} min sin uso baja al brillo {brillo}; las teclas funcionan normal"
        return f"Reposo: tras {minutos} min sin uso se apaga; la primera tecla solo despierta, no ejecuta su acción"

    @staticmethod
    def listarDisponibles() -> list[tuple[str, str]]:
        """(serial, modelo) de los StreamDeck que se pueden agregar a un grupo"""
        return listarStreamDecks(MiStreamDeck.compatibles + MiStreamDeckPlus.compatibles)

    @staticmethod
    def listaDeModelo(modelo: str) -> str:
        """Clave del grupo donde va un StreamDeck de ese modelo; los Plus se conectan después de los normales"""
        return "streamDecksPlus" if modelo in MiStreamDeckPlus.compatibles else "streamDecks"

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

        # brillo antes vivía solo en data/streamdeck.json (lo guarda deck_brillo), se usa si no está en la config
        brillo = dataConfiguracion.get("brillo", ObtenerValor("data/streamdeck.json", "brillo"))
        self.aplicarAparato({**dataConfiguracion, "brillo": 70 if brillo is None else brillo})

    def aplicarAparato(self, data: dict) -> bool:
        """Brillo y reposo se aplican al momento, sin reiniciar"""
        for deckActual in self.listaDeck:
            deckActual.brilloReposo = data.get("brillo_reposo", 0)
            deckActual.minutosReposo = data.get("minutos_reposo", 0)
            deckActual.Brillo(data.get("brillo", deckActual.brillo))
        return True

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
