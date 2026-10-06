# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

import itertools
import threading
import time
from fractions import Fraction

from PIL import Image, ImageSequence
from PIL.Image import Image as ImageImage
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices.StreamDeck import StreamDeck
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError

from elGarrobo.dispositivos import dispositivo
from elGarrobo.dispositivos.dispositivo import grupoBotones
from elGarrobo.dispositivos.dataAccion import dataAccion
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor, SalvarArchivo

logger = ConfigurarLogging(__name__)


# TODO: si re recarga folder borrar _gitCache
class MiStreamDeck(dispositivo):

    modulo = "streamdeck"
    tipo = "streamdeck"
    compatibles = ["Stream Deck Original"]
    # TODO: Agregar mas tipos compatibles

    rotar: int = 0
    "Rota los iconos del botones del teclado"

    baseTeclas: int = 0
    "base inicio del conteo de teclas"
    desfaceTeclas: int = 0
    """Cuantas botones esta adelante del inicio

    ejemplo:
        desface es 10, el segundo botón haría la acción 12
    """
    cantidadBotones: int = 0
    "Cantidad de botones en StreamDeck"
    deck: StreamDeck = None
    idDeck: int = -1
    listaBotones: list[dict] = None
    "lista de información de botones"

    archivoFuente: str = None
    "fuente para texto de botones"

    imagenesBase: dict = None

    pausarDibujando: bool = False
    "Pausar el dibujado mientra se actualiza la información"

    fps: int = 60
    "fotogramas por segundo para gif"

    _gitCache: dict[tuple[str, str, str], itertools.cycle] = {}
    "Caché para Gifs: clave(rutaGif, colorFondo, titulo)"

    _mapaTeclasCache: tuple[list[int], dict[int, int]] = None
    "Caché de (lógico->nativo, nativo->lógico) calculado por _mapaTeclas()"

    def __init__(self, dataConfiguracion: dict) -> None:
        """Inicializando Dispositivo de MiDeckCombinado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """

        super().__init__(dataConfiguracion)
        self.nombre: str = dataConfiguracion.get("nombre", "miStreamDeck")
        self.id = dataConfiguracion.get("id")
        self.fps = dataConfiguracion.get("fps", 60)
        self.rotar = dataConfiguracion.get("rotar", 0)

        self.deckGif = None
        self.layout = None
        self._mapaTeclasCache = None
        self.ultimoDibujo = None
        self.tiempoDibujar: float = 0.4
        self._gitCache = {}
        # self.archivoImagen = None

    def conectar(self) -> bool:
        listaStreamdecks = DeviceManager().enumerate()
        listaIdUsados = dispositivo.listaIndexUsados

        logger.info(f"StreamDeck[Conectándose] - {self.nombre}[{self.dispositivo}]")

        # TODO: Cambiar metodo para cargar StreanDeks
        for idActual, deck in enumerate(listaStreamdecks):

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
                    if self.deck.get_serial_number() == self.dispositivo:
                        self.conectado = True
                        self.cantidadBotones = self.deck.key_count()
                        self.layout = self.deck.key_layout()
                        brillo: int = ObtenerValor("data/streamdeck.json", "brillo")
                        # Todo: brillo no es un int
                        self.deck.set_brightness(brillo)
                        self.deck.set_key_callback(self.actualizarBoton)
                        self.idDeck = idActual
                        dispositivo.agregarIndexUsado(self.idDeck)

                        self.hiloGif = threading.Thread(target=self.animaciónGif)
                        self.hiloGif.start()

                        logger.info(f"StreamDeck[Conectado] - {self.nombre}[{self.deck.get_serial_number()}]")

                        return True
                    else:
                        self.deck.close()

                except TransportError as error:
                    self.conectado = False
                    self.deck = None
                    logger.exception(f"StreamDeck[Error] {self.nombre}[{self.dispositivo}]{error}")
                    return False
                except Exception as error:
                    self.conectado = False
                    self.deck = None
                    logger.exception(f"StreamDeck[Error] {error}")
                    return False
        logger.warning(f"StreamDeck[No encontró] - {self.nombre}")
        self.conectado = False
        return False

    def _mapaTeclas(self) -> tuple[list[int], dict[int, int]]:
        """Mapea índices nativos del StreamDeck a índices lógicos según `rotar`.

        El SDK numera las teclas en su propio layout sin rotar. `rotar` orienta
        físicamente el dispositivo (mismo ángulo que rota los íconos), así que las
        teclas lógicas -las que se usan como `key` en la configuración- quedan
        numeradas en orden de lectura (arriba-abajo, izquierda-derecha) sobre el
        layout ya rotado, en vez del orden nativo del SDK.

        Returns:
            tuple[list[int], dict[int, int]]: lista lógico->nativo, dict nativo->lógico
        """

        if self._mapaTeclasCache is not None:
            return self._mapaTeclasCache

        filas, columnas = self.layout
        grid = [[fila * columnas + columna for columna in range(columnas)] for fila in range(filas)]

        pasos = (self.rotar // 90) % 4
        for _ in range(pasos):
            grid = [list(fila) for fila in zip(*grid[::-1])]

        logicoANativo = [nativo for fila in grid for nativo in fila]
        nativoALogico = {nativo: logico for logico, nativo in enumerate(logicoANativo)}

        self._mapaTeclasCache = (logicoANativo, nativoALogico)
        return self._mapaTeclasCache

    def actualizarIconos(self) -> None:
        """Refresca iconos, tomando en cuenta pagina actual."""
        if not self.conectado:
            return

        if self.deck is None or not self.deck.is_open():
            self.conectado = False
            return

        if self.listaAcciones is None:
            self.limpiarIconos()
            # Borrar todo los botones
            return

        if self.listaBotones is None:
            self.listaBotones = list()
            for _ in range(self.cantidadBotones):
                data = {
                    "imagen": None,
                    "titulo": None,
                    "gif": None,
                }
                self.listaBotones.append(data)

        # tiempoActual = time.time()

        # if self.ultimoDibujo is None:
        #     self.ultimoDibujo = -self.tiempoDibujar

        # if tiempoActual - self.ultimoDibujo < self.tiempoDibujar:
        #     print(tiempoActual - self.ultimoDibujo, self.tiempoDibujar)
        #     return

        logger.info(f"Deck[Dibujar] {self.nombre}")

        self.actualizarDataFolder()

        _, nativoALogico = self._mapaTeclas()

        self.pausarDibujando = True
        for i in range(self.cantidadBotones):
            botonDesface: int = nativoALogico[i] + self.baseTeclas + self.desfaceTeclas

            dibujar = list(filter(lambda accion: accion.get("key") == botonDesface, self.listaAcciones))

            if dibujar:
                accionActual: dict = dibujar[0]
                accionVieja = self.listaBotones[i]

                dibujo = self.dibujo()
                imagenActual: str = dibujo.buscarDireccionImagen(accionActual)
                tituloActual: str = dibujo.buscarTitulo(accionActual)
                # Copia: se compara con lo dibujado para redibujar si cambia fondo, rotar, etc.
                opcionesActual: dict = dict(accionActual.get("imagen_opciones") or {})

                imagenVieja: str = accionVieja.get("imagen")
                tituloViejo: str = accionVieja.get("titulo")

                if imagenActual == imagenVieja and tituloActual == tituloViejo and opcionesActual == accionVieja.get("opciones"):
                    continue

                accionVieja["imagen"] = imagenActual
                accionVieja["titulo"] = tituloActual
                accionVieja["opciones"] = opcionesActual

                if imagenActual is not None and imagenActual.endswith(".gif"):
                    accionVieja["gif"] = self.crearGif(i, accionActual)
                else:
                    self.actualizarIconoBoton(i, accionActual)
                    accionVieja["gif"] = None
            else:
                self.listaBotones[i] = {
                    "imagen": None,
                    "titulo": None,
                    "gif": None,
                }
                self.limpiarIcono(i)
        self.pausarDibujando = False

    def limpiarIconos(self) -> None:
        """Borra iconos de todo los botones de StreamDeck."""
        if self.conectado:
            logger.info(f"Limpiando {self.nombre}")
            # self.deckGif.Limpiar()
            for i in range(self.cantidadBotones):
                self.limpiarIcono(i)
            self.archivoImagen = None

    def limpiarIcono(self, indice: int) -> None:
        """Limpia un botón con una imagen negro

        Args:
            indice (int): Botón a borrar la imagen
        """

        fondo: str = "black"

        if self.propiedadFolder:
            opcionesFolder = (self.propiedadFolder or {}).get("imagen_opciones") or {}
            fondo = opcionesFolder.get("fondo") or fondo

        imagenNegro = PILHelper.create_image(self.deck, fondo)
        self.deck.set_key_image(indice, PILHelper.to_native_format(self.deck, imagenNegro))

    def Brillo(self, Brillo):
        """Cambia brillo de StreamDeck."""
        if self.conectado:
            self.deck.set_brightness(Brillo)

    def actualizarBoton(self, deck, key, estado) -> None:

        _, nativoALogico = self._mapaTeclas()
        numeroTecla = nativoALogico[key] + self.baseTeclas + self.desfaceTeclas
        if estado:
            self.buscarAccion(numeroTecla, self.estadoTecla.PRESIONADA)
        else:
            self.buscarAccion(numeroTecla, self.estadoTecla.LIBERADA)

    def actualizar(self) -> None:
        if self.recargar:
            self.actualizarIconos()
        super().actualizar()

    def desconectar(self) -> None:
        if self.conectado:
            logger.info(f"Deck[Desconectando] - {self.nombre}")
            self.conectado = False
            self.deck.reset()
            self.deck.close()

    def __str__(self) -> str:
        return f"MiStreamDeck(id={self.id}, nombre={self.nombre}, serial={self.dispositivo}, layout={self.layout})"

    def gruposBotones(self) -> list[grupoBotones]:
        """Teclas como se ven con el StreamDeck rotado: un 3x5 con rotar ±90 se ve 5x3"""
        # ponytail: sin conectar no se sabe el layout, se asume StreamDeck Original 3x5
        filas, columnas = self.layout or (3, 5)
        if (self.rotar // 90) % 2:
            filas, columnas = columnas, filas
        return [grupoBotones(self.nombre, filas, columnas, self.baseTeclas + self.desfaceTeclas, self)]

    def tamañoBoton(self) -> tuple[int, int]:
        """Tamaño en pixeles de las teclas, 72x72 (StreamDeck Original) si no está conectado"""
        if self.deck is None:
            return super().tamañoBoton()
        return self.deck.key_image_format()["size"]

    def actualizarIconoBoton(self, indice: int, accionActual: dict) -> None:
        """Dibuja la información de un botón en base la accion.
        Usando imagen, titulo y otra información para mostrar en steamdeck

        Args:
            indice [int]: id del botón a actualizar
            accionActual [dict]: información de la accion
        """
        imagenBoton: ImageImage = self.dibujo().dibujar(accionActual, self.tamañoBoton())
        self.deck.set_key_image(indice, PILHelper.to_native_format(self.deck, imagenBoton))

    @staticmethod
    def iniciarTituloMQTT() -> None:
        """Inicializa el título MQTT, creando el archivo si no existe."""
        archivoTituloMQTT: str = "data/tituloMQTT"
        SalvarArchivo(archivoTituloMQTT, {})

    def crearGif(self, indice: int, accionActual: dict) -> itertools.cycle:
        """Preparar el git para usar con StreamDeck

        Args:
            indice (int): id del botón
            accionActual (dict): Información del botón

        Returns:
            itertools.cycle: lista de imagen listos para mostrarse en StreamDeck
        """

        listaFrame: list = list()
        colorFondo: str = "black"
        dibujo = self.dibujo()
        rutaGif: str = dibujo.buscarDireccionImagen(accionActual)

        rutaGif = dibujo.calcularRutaImagen(rutaGif)

        if rutaGif is None:
            logger.warning(f"{self.nombre}[No Gifs] {indice + self.baseTeclas + self.desfaceTeclas} {rutaGif}")
            return

        opciones = accionActual.get("imagen_opciones")

        if opciones:
            colorFondo = opciones.get("fondo") or colorFondo

        titulo = dibujo.buscarTitulo(accionActual)

        claveCache = (str(rutaGif), str(colorFondo), str(titulo))

        if claveCache in self._gitCache:
            return self._gitCache[claveCache]

        cargarGif = Image.open(rutaGif)
        for frame in ImageSequence.Iterator(cargarGif):
            frameActual = PILHelper.create_scaled_image(self.deck, frame, background=colorFondo)

            if titulo:
                dibujo.ponerTexto(frameActual, titulo, accionActual, (rutaGif, str))

            frameActual = frameActual.rotate(self.rotar, resample=Image.BICUBIC, expand=False)
            imagenNativa = PILHelper.to_native_format(self.deck, frameActual)

            listaFrame.append(imagenNativa)

        listaFrame: itertools.cycle = itertools.cycle(listaFrame)

        self._gitCache[claveCache] = listaFrame

        return listaFrame

    def animaciónGif(self) -> None:
        """ """

        tiempoFrame = Fraction(1, self.fps)
        siguienteFrame = Fraction(time.monotonic())

        while self.deck.is_open():
            if not self.pausarDibujando and self.listaBotones is not None:
                try:
                    with self.deck:
                        for i, accionActual in enumerate(self.listaBotones):
                            frames = accionActual.get("gif")
                            if not frames:
                                continue
                            self.deck.set_key_image(i, next(frames))
                except TransportError as err:
                    logger.info(f"StreamDeck[Desconectado] - {self.nombre} durante animación: {err}")
                    break

            siguienteFrame += tiempoFrame

            tiempoEspera = float(siguienteFrame) - time.monotonic()

            if tiempoEspera >= 0:
                time.sleep(tiempoEspera)

    def actualizarDataFolder(self) -> None:
        """Actualiza las propiedades de folder para los botones."""

        self.propiedadFolder = dict()

        for accion in self.listaAcciones:
            if not isinstance(accion, (dict, dataAccion)):
                continue
            if accion.get("key") == "propiedad_folder":
                self.propiedadFolder = accion
                break
