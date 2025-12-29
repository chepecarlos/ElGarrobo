# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

import itertools
import os
import threading
import time
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices.StreamDeck import StreamDeck
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError

from elGarrobo.dispositivos import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor

logger = ConfigurarLogging(__name__)


class MiStreamDeck(dispositivo):

    modulo = "streamdeck"
    tipo = "streamdeck"
    compatibles = ["Stream Deck Original"]
    # TODO: Agregar mas tipos compatibles

    baseTeclas: int = None
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
    "lista de informacion de botones"

    archivoFuente: str = None
    "fuente para texto de botones"

    imagenesBase: dict = None

    pausarDibujando: bool = False
    "Pausar el dibujado mientra se actualiza la información"

    fps: int = 60
    "fotogramas por segundo para gif"

    def __init__(self, dataConfiguracion: dict) -> None:
        """Inicializando Dispositivo de MiDeckCombinado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """

        super().__init__(dataConfiguracion)
        self.nombre: str = dataConfiguracion.get("nombre", "miStreamDeck")
        self.id = dataConfiguracion.get("id")
        self.fps = dataConfiguracion.get("fps", 60)

        self.deckGif = None
        self.layout = None
        self.ultimoDibujo = None
        self.tiempoDibujar: float = 0.4
        # self.archivoImagen = None

    def conectar(self):
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

                        return
                    else:
                        self.deck.close()

                except TransportError as error:
                    self.conectado = False
                    self.deck = None
                    logger.exception(f"StreamDeck[Error] {self.nombre}[{self.dispositivo}]{error}")
                    return
                except Exception as error:
                    self.conectado = False
                    self.deck = None
                    logger.exception(f"StreamDeck[Error] {error}")
                    return
        logger.warning(f"StreamDeck[No encontró] - {self.nombre}")
        self.conectado = False

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
        self.pausarDibujando = True
        for i in range(self.cantidadBotones):
            botonDesface: int = i + self.baseTeclas + self.desfaceTeclas

            dibujar = list(filter(lambda accion: accion.get("key") == botonDesface, self.listaAcciones))

            if dibujar:
                accionActual: dict = dibujar[0]
                accionVieja = self.listaBotones[i]

                imagenActual: str = self.buscarDirecionImagen(accionActual)
                tituloActual: str = self.buscarTitulo(accionActual)

                imagenVieja: str = accionVieja.get("imagen")
                tituloViejo: str = accionVieja.get("titulo")

                if imagenActual == imagenVieja and tituloActual == tituloViejo:
                    continue

                accionVieja["imagen"] = imagenActual
                accionVieja["titulo"] = tituloActual

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

    def limpiarIconos(self):
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
            indice: int
        """
        imagenNegro = PILHelper.create_image(self.deck)
        self.deck.set_key_image(indice, PILHelper.to_native_format(self.deck, imagenNegro))

    def Brillo(self, Brillo):
        """Cambia brillo de StreamDeck."""
        if self.conectado:
            self.deck.set_brightness(Brillo)

    def actualizarBoton(self, Deck, key, estado) -> None:
        numeroTecla = key + self.baseTeclas + self.desfaceTeclas
        if estado:
            self.buscarAccion(numeroTecla, self.estadoTecla.PRESIONADA)
        else:
            self.buscarAccion(numeroTecla, self.estadoTecla.LIBERADA)

    def desconectar(self) -> None:
        if self.conectado:
            logger.info(f"Deck[Desconectando] - {self.nombre}")
            self.conectado = False
            self.deck.reset()
            self.deck.close()

    def __str__(self) -> str:
        return f"MiStreamDeck(id={self.id}, nombre={self.nombre}, serial={self.dispositivo}, layout={self.layout})"

    def actualizarIconoBoton(self, indice: int, accionActual: dict):

        colorFondo: str = "black"

        opciones = accionActual.get("imagen_opciones")
        if opciones:
            if "fondo" in opciones:
                colorFondo = opciones["fondo"]

        ImagenDeck: Image = PILHelper.create_image(self.deck, background=colorFondo)

        ImagenBoton: Image = self.obtenerImagen(ImagenDeck, accionActual)

        self.deck.set_key_image(indice, PILHelper.to_native_format(self.deck, ImagenBoton))

    def obtenerImagen(self, imagen: Image, accion: dict) -> Image:
        modificado: bool = False
        imagenFondo = None

        if "imagen_opciones" in accion:
            opciones = accion["imagen_opciones"]
            if "fondo" in opciones:
                ColorFondo = opciones["fondo"]
                # TODO: Agregar color de fondo
            if "imagen" in opciones:
                imagenFondo = opciones["imagen"]
                modificado = True

        if imagenFondo is not None:
            modificado = True
            self.ponerImagen(imagen, imagenFondo, accion, True)

        DirecionImagen: str = self.buscarDirecionImagen(accion)

        if DirecionImagen is not None:
            modificado = True
            if DirecionImagen.endswith(".gif"):
                # TODO: Meter proceso gif adentro
                return None

        self.ponerImagen(imagen, DirecionImagen, accion)

        tituloBoton: str = self.buscarTitulo(accion)

        if tituloBoton is not None:
            modificado = True
            self.ponerTexto(imagen, tituloBoton, accion, isinstance(DirecionImagen, str))

        return imagen

    def buscarTitulo(self, accion: dict) -> str | None:
        """Busca el título para el botón

        Args:
            accion (dict): Datos de la acción del botón

        Returns:
            str | None: Título encontrado o None
        """

        titulo: str = None

        TextoCargar = accion.get("cargar_titulo")
        if TextoCargar is not None:
            archivoTexto = TextoCargar.get("archivo")
            atributoTexto = TextoCargar.get("atributo")
            if archivoTexto is not None and atributoTexto is not None:
                titulo = ObtenerValor(archivoTexto, atributoTexto)
                return titulo

        if "titulo" in accion:
            titulo: str = str(accion.get("titulo"))

        opciones: dict = accion.get("titulo_opciones", dict())
        if opciones is None:
            opciones = dict()

        topicTituloMQTT: str = opciones.get("mqtt", False)

        if topicTituloMQTT:
            tituloMQTT = self.obtenerTituloMQTT(topicTituloMQTT, titulo)

            if "{}" in titulo and titulo != tituloMQTT:
                titulo = titulo.format(tituloMQTT)
            else:
                titulo = tituloMQTT

        return titulo

    def calcularRutaImagen(self, rutaImagen: str) -> str:
        """Calcula la Ruta absoluta de imagen

        Args:
            rutaImagen (str): ruta relativa de la imagen

        Returns:
            str: ruta absoluta de la imagen
        """

        folderPerfil = self._folderConfigPerfil()
        # folderActual = Path(self.folderActual)

        pathImagen = Path(rutaImagen)

        if rutaImagen.startswith("/"):
            pathImagen = folderPerfil / rutaImagen.lstrip("/")
        else:
            pathImagen = folderPerfil / self.folderActual / pathImagen

        return str(pathImagen.resolve())

    def ponerImagen(self, Imagen: Image, NombreIcono: str, accion, fondo: bool = False):
        if NombreIcono is None:
            return

        DirecionIcono = self.calcularRutaImagen(NombreIcono)

        if os.path.exists(DirecionIcono):
            Icono = Image.open(DirecionIcono).convert("RGBA")
            if "titulo" in accion and not fondo:
                Icono.thumbnail((Imagen.width, Imagen.height - 20), Image.LANCZOS)
            else:
                Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)
        else:
            logger.warning(f"Deck[No Imagen] {NombreIcono} - {DirecionIcono}")
            Icono = Image.new(mode="RGBA", size=(256, 256), color=(153, 153, 255))
            Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)

        IconoPosicion = ((Imagen.width - Icono.width) // 2, 0)
        Imagen.paste(Icono, IconoPosicion, Icono)

    def ponerTexto(self, Imagen, titulo: str, accion: dict, hayImagen: bool = False, cortePalabra: bool = False):
        """Agrega Texto a Botones de StreamDeck.

        Args:
            Imagen (Image): Imagen del botón
            accion (dict): Datos de la acción del botón
            hayImagen (bool, optional): Si ya tiene imagen el botón. Defaults to False.
        """

        TituloInicial: str = titulo
        opciones: dict = accion.get("titulo_opciones", dict())
        if opciones is None:
            opciones = dict()
        tamañoFuente: int = opciones.get("tamanno", 40)
        alinear: str = opciones.get("alinear", "centro")
        Borde_Color: str = opciones.get("borde_color", "black")
        Borde_Grosor: int = opciones.get("borde_grosor", 6)
        Ajustar: bool = opciones.get("ajustar", True)
        Titulo_Color: str = opciones.get("color", "white")

        Lineas = TituloInicial.split("\\n")
        Titulo = "\n".join(Lineas)
        if cortePalabra:
            Lineas = Titulo.split(" ")
            Titulo = "\n".join(Lineas)
        espacioLinea: int = 1

        dibujo: ImageDraw = ImageDraw.Draw(Imagen)

        tamañoMinimo: int = None
        if hayImagen:
            alinear = "abajo"
            tamañoMinimo = 20

        tamañoFuente, altoTitulo, anchoTitulo = self.calcularTamañoFuente(Imagen, Titulo, Borde_Grosor, espacioLinea, tamañoMinimo)

        fuente = ImageFont.truetype(self.archivoFuente, size=tamañoFuente)

        textoX = (Imagen.width - anchoTitulo) / 2 + Borde_Grosor

        if alinear == "centro":
            textoY = (Imagen.height - altoTitulo) / 2
        elif alinear == "ariba":
            textoY = 0
        else:
            textoY = Imagen.height - altoTitulo

        posicionTexto = (textoX, textoY)

        dibujo.multiline_text(
            posicionTexto,
            text=Titulo,
            font=fuente,
            fill=Titulo_Color,
            stroke_width=Borde_Grosor,
            stroke_fill=Borde_Color,
            align="center",
            spacing=espacioLinea,
        )

    def calcularTamañoFuente(self, imagen: ImageDraw, texto: str, grosorBorde: int, espacioLinea: int, minimo: int | None) -> tuple[int, int, int]:
        """Calcula tamaño de fuente para texto en botón de StreamDeck.

        Args:
            imagen (ImageDraw): Imagen del botón
            texto (str): Texto a colocar en el botón
            grosorBorde (int): Grosor del borde del texto
            espacioLinea (int): Espacio entre líneas del texto
            minimo (int | None): Tamaño mínimo de fuente

        Returns:
            tuple[int, int, int]: Tamaño de fuente, alto del texto y ancho del texto
        """

        anchoImagen, altoImagen = imagen.width, imagen.height

        tamañoFuente = 100
        dibujo: ImageDraw = ImageDraw.Draw(imagen)

        fuentePrueba = ImageFont.truetype(self.archivoFuente, size=tamañoFuente)
        cajaTexto = dibujo.multiline_textbbox(
            xy=[0, 0],
            text=texto,
            font=fuentePrueba,
            align="center",
            spacing=espacioLinea,
            stroke_width=grosorBorde,
        )

        anchoTitulo = cajaTexto[2] - cajaTexto[0]
        altoTitulo = cajaTexto[3] - cajaTexto[1]

        calculoAncho = anchoImagen / anchoTitulo
        calculoAlto = altoImagen / altoTitulo

        escala = min(calculoAncho, calculoAlto)

        tamañoCalculo = int(tamañoFuente * escala)

        tamañoFuente = max(3, tamañoCalculo)

        if minimo is not None:
            tamañoFuente = min(minimo, tamañoFuente)

        fuentePrueba = ImageFont.truetype(self.archivoFuente, size=tamañoFuente)
        cajaTexto = dibujo.multiline_textbbox(
            xy=[0, 0],
            text=texto,
            font=fuentePrueba,
            align="center",
            spacing=espacioLinea,
            stroke_width=grosorBorde,
        )

        anchoTitulo = cajaTexto[2] - cajaTexto[0]
        altoTitulo = cajaTexto[3] - cajaTexto[1]

        return tamañoFuente, altoTitulo, anchoTitulo

    def buscarDirecionImagen(self, accion: dict) -> str | None:
        """Busca la direccion de imagen

        Args:
            accion: dict
        """

        if "imagen_estado" in accion:

            imagenEstado = accion.get("imagen_estado")
            nombreAccion = accion.get("accion")
            opcionesAccion = accion.get("opciones")

            if nombreAccion.startswith("obs"):
                estadoImagen = self.BuscarImagenOBS(nombreAccion, opcionesAccion)
                if estadoImagen:
                    DirecionImagen = imagenEstado.get("imagen_true")
                else:
                    DirecionImagen = imagenEstado.get("imagen_false")

                return DirecionImagen

        if "imagen" in accion:
            DirecionImagen = accion.get("imagen")
            return DirecionImagen
        elif "accion" in accion:
            nombreAccion = accion.get("accion")
            if nombreAccion in self.imagenesBase:
                return self.imagenesBase[nombreAccion]

        return None

    def BuscarImagenOBS(self, NombreAccion: str, opcionesAccion: dict) -> bool | None:
        Estado = None

        ListaBasicas = ["obs_conectar", "obs_grabar", "obs_pausar", "obs_envivo", "obs_camara_virtual", "obs_grabar_vertical"]
        for Basica in ListaBasicas:
            if NombreAccion == Basica:
                Estado = ObtenerValor("data/obs/obs", Basica)

        if NombreAccion == "obs_escena":
            if "escena" in opcionesAccion:
                EscenaActual = opcionesAccion["escena"]
                EscenaActiva = ObtenerValor("data/obs/obs", "obs_escena")
                if EscenaActual == EscenaActiva:
                    Estado = True
                else:
                    Estado = False
        elif NombreAccion == "obs_fuente":
            if "fuente" in opcionesAccion:
                FuenteActual = opcionesAccion["fuente"]
                Estado = ObtenerValor("data/obs/obs_fuente", FuenteActual)
        elif NombreAccion == "obs_filtro":
            if "fuente" in opcionesAccion:
                Fuente = opcionesAccion["fuente"]
            if "filtro" in opcionesAccion:
                Filtro = opcionesAccion["filtro"]
            if Fuente is not None and Filtro is not None:
                Estado = ObtenerValor("data/obs/obs_filtro", [Fuente, Filtro])

        if Estado is None:
            Estado = False

        return Estado

    def obtenerTituloMQTT(self, topicTitulo: str, tituloInicial: str = "") -> str:
        """Obtiene el titulo enviado por MQTT

        Args:
            topicTitulo (str): Cual topic hay que leer

        Returns:
            str: devuelve el titulo encontrado
        """

        archivoTituloMQTT: str = "data/tituloMQTT"

        titulo = ObtenerValor(archivoTituloMQTT, topicTitulo)
        if titulo is None:
            return tituloInicial
        return titulo

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
        rutaGif: str = self.buscarDirecionImagen(accionActual)

        rutaGif = self.calcularRutaImagen(rutaGif)

        if rutaGif is None:
            logger.warning(f"{self.nombre}[No Gifs] {indice + self.baseTeclas + self.desfaceTeclas} {rutaGif}")
            return

        opciones = accionActual.get("imagen_opciones")

        if opciones:
            colorFondo = opciones.get("fondo") or colorFondo

        cargarGif = Image.open(rutaGif)
        for frame in ImageSequence.Iterator(cargarGif):
            frameActual = PILHelper.create_scaled_image(self.deck, frame, background=colorFondo)

            titulo = self.buscarTitulo(accionActual)

            if titulo:
                self.ponerTexto(frameActual, titulo, accionActual, (rutaGif, str))

            imagenNativa = PILHelper.to_native_format(self.deck, frameActual)

            listaFrame.append(imagenNativa)

        listaFrame: itertools.cycle = itertools.cycle(listaFrame)

        return listaFrame

    def animaciónGif(self) -> None:

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
                    print("TransportError: {0}".format(err))
                    break

            siguienteFrame += tiempoFrame

            tiempoEspera = float(siguienteFrame) - time.monotonic()

            if tiempoEspera >= 0:
                time.sleep(tiempoEspera)
