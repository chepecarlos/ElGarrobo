# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

import copy
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
from elGarrobo.miLibrerias import ConfigurarLogging, SalvarArchivo

logger = ConfigurarLogging(__name__)


# TODO: si re recarga folder borrar _gifCache
class MiStreamDeck(dispositivo):

    modulo = "streamdeck"
    tipo = "streamdeck"
    compatibles = ["Stream Deck Original"]
    # TODO: Agregar mas tipos compatibles

    rotar: int = 0
    "Rota los iconos del botones del teclado"

    baseTeclas: int = 0
    "base inicio del conteo de teclas"
    desfaseTeclas: int = 0
    """Cuantas botones esta adelante del inicio

    ejemplo:
        desfase es 10, el segundo botón haría la acción 12
    """
    cantidadBotones: int = 0
    "Cantidad de botones en StreamDeck"
    deck: StreamDeck = None
    apagando: bool = False
    "desconectar() lo pide, no reconectar"
    esperaReconectar: float = 3
    "segundos entre intentos de reconexión"
    listaBotones: list[dict] = None
    "lista de información de botones"

    archivoFuente: str = None
    "fuente para texto de botones"

    imagenesBase: dict = None

    pausarDibujando: bool = False
    "Pausar el dibujado mientra se actualiza la información"

    fps: int = 60
    "fotogramas por segundo para gif"

    brillo: int = 70
    "brillo normal (0-100)"
    brilloReposo: int = 0
    "brillo en reposo (0-100), como el modo reposo de la app oficial para cuidar las pantallas"
    minutosReposo: float = 0
    "minutos sin tocar nada para entrar en reposo, 0 lo desactiva"
    enReposo: bool = False

    _gifCache: dict[tuple[str, str, str], itertools.cycle] = {}
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
        self._gifCache = {}
        self._teclaDespertar = None
        # self.archivoImagen = None

    def conectar(self) -> bool:
        logger.info(f"StreamDeck[Conectándose] - {self.nombre}[{self.dispositivo}]")

        # ponytail: se prueban todos los compatibles por serial; los que ya usa otro MiStreamDeck
        # fallan al abrir (libusb los tiene reclamados) y se saltan
        for deck in DeviceManager().enumerate():

            if deck.DECK_TYPE not in self.compatibles:
                continue

            try:
                deck.open()
                if deck.get_serial_number() != self.dispositivo:
                    deck.close()
                    continue
                # reset después del serial, si no borra las imágenes de otro StreamDeck del mismo modelo
                deck.reset()
                self.deck = deck
                self.conectado = True
                self.apagando = False
                self.listaBotones = None
                self.cantidadBotones = self.deck.key_count()
                self.layout = self.deck.key_layout()
                self.deck.set_brightness(self.brillo)
                self.enReposo = False
                dispositivo.ultimaActividad = time.monotonic()
                self.deck.set_key_callback(self.actualizarBoton)

                self.hiloGif = threading.Thread(target=self.animaciónGif, daemon=True)
                self.hiloGif.start()

                logger.info(f"StreamDeck[Conectado] - {self.nombre}[{self.dispositivo}]")
                return True
            except TransportError as error:
                logger.debug(f"StreamDeck[Saltando] {self.nombre}: {error}")
                if deck.is_open():
                    deck.close()
            except Exception as error:
                logger.exception(f"StreamDeck[Error] {self.nombre}: {error}")
                if deck.is_open():
                    deck.close()
        logger.warning(f"StreamDeck[No encontró] - {self.nombre}")
        self.conectado = False
        return False

    def reconectar(self) -> None:
        """Espera a que vuelva el StreamDeck después de una desconexión USB y lo redibuja"""
        logger.warning(f"StreamDeck[Desconectado] - {self.nombre}, intentando reconectar")
        self.conectado = False
        try:
            self.deck.close()
        except Exception:
            pass

        while not self.apagando:
            time.sleep(self.esperaReconectar)
            if self.apagando:
                return
            if self.conectar():
                self.actualizarIconos()
                return

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


        _, nativoALogico = self._mapaTeclas()

        self.pausarDibujando = True
        for i in range(self.cantidadBotones):
            botonDesfase: int = nativoALogico[i] + self.baseTeclas + self.desfaseTeclas

            dibujar = list(filter(lambda accion: accion.get("key") == botonDesfase, self.listaAcciones))

            if dibujar:
                accionActual: dict = dibujar[0]
                accionVieja = self.listaBotones[i]

                dibujo = self.dibujo()
                imagenActual: str = dibujo.buscarDireccionImagen(accionActual)
                tituloActual: str = dibujo.buscarTitulo(accionActual)
                opcionesActual = self.opcionesDibujo(accionActual)

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
        """Cambia brillo normal de StreamDeck; en reposo se aplica al despertar"""
        self.brillo = Brillo
        if self.conectado and not self.enReposo:
            with self.deck:
                self.deck.set_brightness(Brillo)

    def buscarAccion(self, tecla: str, estado=dispositivo.estadoTecla.PRESIONADA, fuerza: int = 1) -> None:
        """Toda entrada (teclas, diales, táctil) cuenta como actividad para el reposo, igual que en otros dispositivos.

        Con brilloReposo 0 no se ven los íconos, así que la tecla solo despierta y su soltar también se ignora;
        con brillo bajo se alcanzan a ver y la tecla se ejecuta normal.
        """
        dispositivo.ultimaActividad = time.monotonic()
        if self.enReposo and not self.brilloReposo:
            if estado == self.estadoTecla.PRESIONADA:
                self._teclaDespertar = tecla
            return
        if self._teclaDespertar == tecla and estado == self.estadoTecla.LIBERADA:
            self._teclaDespertar = None
            return
        super().buscarAccion(tecla, estado, fuerza)

    def revisarReposo(self) -> None:
        """Baja el brillo tras `minutosReposo` sin tocar ningún dispositivo y lo regresa al tocar uno"""
        reposo = bool(self.minutosReposo) and time.monotonic() - dispositivo.ultimaActividad > self.minutosReposo * 60
        if reposo == self.enReposo:
            return
        with self.deck:
            self.deck.set_brightness(self.brilloReposo if reposo else self.brillo)
        self.enReposo = reposo
        logger.info(f"StreamDeck[{'Reposo' if reposo else 'Despierto'}] - {self.nombre}")

    def actualizarBoton(self, deck, key, estado) -> None:

        _, nativoALogico = self._mapaTeclas()
        numeroTecla = nativoALogico[key] + self.baseTeclas + self.desfaseTeclas
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
            self.apagando = True
            self.conectado = False
            self.deck.reset()
            self.deck.close()

    def __str__(self) -> str:
        return f"MiStreamDeck(id={self.id}, nombre={self.nombre}, serial={self.dispositivo}, layout={self.layout})"

    layoutDefecto: tuple[int, int] = (3, 5)
    "Filas y columnas que se dibujan en la GUI mientras no está conectado"

    def gruposBotones(self) -> list[grupoBotones]:
        """Teclas como se ven con el StreamDeck rotado: un 3x5 con rotar ±90 se ve 5x3"""
        # ponytail: sin conectar no se sabe el layout, se asume el del modelo (Original 3x5, Plus 2x4)
        filas, columnas = self.layout or self.layoutDefecto
        if (self.rotar // 90) % 2:
            filas, columnas = columnas, filas
        return [grupoBotones(self.nombre, filas, columnas, self.baseTeclas + self.desfaseTeclas, self)]

    def opcionesDibujo(self, accion) -> tuple:
        """Copia de las opciones que cambian el dibujo de un botón (las suyas y las del folder),
        se compara con lo ya dibujado para redibujar si cambia fondo, rotar, tamaño del título, etc."""
        propiedadFolder = self.propiedadFolder
        return copy.deepcopy(
            (
                accion.get("imagen_opciones"),
                accion.get("titulo_opciones"),
                propiedadFolder.aDict() if propiedadFolder is not None else None,
            )
        )

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
        """Preparar el gif para usar con StreamDeck

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
            logger.warning(f"{self.nombre}[No Gifs] {indice + self.baseTeclas + self.desfaseTeclas} {rutaGif}")
            return

        opciones = accionActual.get("imagen_opciones")

        if opciones:
            colorFondo = opciones.get("fondo") or colorFondo

        titulo = dibujo.buscarTitulo(accionActual)

        claveCache = (str(rutaGif), str(colorFondo), str(titulo))

        if claveCache in self._gifCache:
            return self._gifCache[claveCache]

        cargarGif = Image.open(rutaGif)
        for frame in ImageSequence.Iterator(cargarGif):
            # Misma función que la vista previa de la GUI
            frameActual = dibujo.dibujarCuadroGif(accionActual, frame, self.tamañoBoton(), self.rotar)
            imagenNativa = PILHelper.to_native_format(self.deck, frameActual)

            listaFrame.append(imagenNativa)

        listaFrame: itertools.cycle = itertools.cycle(listaFrame)

        self._gifCache[claveCache] = listaFrame

        return listaFrame

    def animaciónGif(self) -> None:
        """ """

        tiempoFrame = Fraction(1, self.fps)
        siguienteFrame = Fraction(time.monotonic())

        while self.deck.is_open():
            try:
                self.revisarReposo()
                # En reposo no se animan los gifs, no se ven y se ahorra USB
                if not self.pausarDibujando and not self.enReposo and self.listaBotones is not None:
                    with self.deck:
                        for i, accionActual in enumerate(self.listaBotones):
                            frames = accionActual.get("gif")
                            if not frames:
                                continue
                            self.deck.set_key_image(i, next(frames))
            except TransportError as err:
                logger.info(f"StreamDeck[Error] - {self.nombre} durante animación: {err}")
                break

            siguienteFrame += tiempoFrame

            tiempoEspera = float(siguienteFrame) - time.monotonic()

            if tiempoEspera >= 0:
                time.sleep(tiempoEspera)

        if not self.apagando:
            self.reconectar()
