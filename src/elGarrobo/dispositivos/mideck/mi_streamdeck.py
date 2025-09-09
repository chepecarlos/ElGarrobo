# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

import os
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError

from elGarrobo.dispositivos.dispositivoBase import dispositivoBase
from elGarrobo.miLibrerias import (
    ConfigurarLogging,
    ObtenerArchivo,
    ObtenerFolderConfig,
    ObtenerValor,
    RelativoAbsoluto,
    UnirPath,
)

# from .mi_deck_extra import BuscarDirecionImagen
from .mi_deck_gif import DeckGif
from .mi_deck_imagen import ActualizarIcono, LimpiarIcono

logger = ConfigurarLogging(__name__)


class MiStreamDeck(dispositivoBase):

    modulo = "streamdeck"
    tipo = "streamdeck"

    baseTeclas: int = None
    "base inicio del conteo de teclas"
    desfaceTeclas: int = 0
    """Cuantas botones esta adelante del inicio
    
    ejemplo:
        desface es 10, el segundo botón haría la acción 12 
    """
    cantidadBotones: int = 0
    "Cantidad de botones en StreamDeck"
    deck: DeviceManager = None
    idDeck: int = -1

    archivoFuente: str = None
    "fuente para texto de botones"

    imagenesBase: dict = None

    def __init__(self, dataConfiguracion: dict):
        """Inicializando Dispositivo de MiDeckCombinado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """

        super().__init__()
        self.id = dataConfiguracion.get("id")
        self.nombre: str = dataConfiguracion.get("nombre")
        self.dispositivo: str = dataConfiguracion.get("dispositivo")
        self.archivo = dataConfiguracion.get("archivo", "")
        self.DeckGif = None
        self.layout = None
        self.ultimoDibujo = None
        self.tiempoDibujar: float = 0.4
        self.archivoImagen = None

    def conectar(self):
        listaStreamdecks = DeviceManager().enumerate()
        listaIdUsados = dispositivoBase.listaIndexUsados

        logger.info(f"StreamDeck[Conectándose] - {self.nombre}[{self.dispositivo}]")

        # TODO: Cambiar metodo para cargar StreanDeks
        for idActual, deck in enumerate(listaStreamdecks):
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
                        Brillo = ObtenerValor("data/streamdeck.json", "brillo")
                        # Todo: brillo no es un int
                        self.deck.set_brightness(Brillo)
                        self.DeckGif = DeckGif(self.deck, self.folderActual)
                        self.DeckGif.start()
                        self.deck.set_key_callback(self.actualizarBoton)
                        self.idDeck = idActual
                        dispositivoBase.agregarIndexUsado(self.idDeck)
                        logger.info(f"StreamDeck[Conectado] - {self.nombre}")

                        # self.actualizarIconos()

                        return
                    else:
                        self.deck.close()

                except TransportError as error:
                    self.conectado = False
                    self.deck = None
                    logger.exception(f"StreamDeck[Error] {self.nombre}[{self.dispositivo}]{error}")
                except Exception as error:
                    self.conectado = False
                    self.deck = None
                    logger.exception(f"StreamDeck[Error] {error}")

    def actualizarIconos(self, acciones: dict = False, desface: int = False, Unido: bool = False):
        """Refresca iconos, tomando en cuenta pagina actual."""
        if not self.conectado:
            return

        if self.listaAcciones is None:
            return

        if self.archivoImagen is None:
            self.archivoImagen = list()
            for _ in range(self.cantidadBotones):
                self.archivoImagen.append("")

        if self.deck is None or not self.deck.is_open():
            self.conectado = False
            return

        tiempoActual = time.time()

        if self.ultimoDibujo is None:
            self.ultimoDibujo = -self.tiempoDibujar

        if tiempoActual - self.ultimoDibujo < self.tiempoDibujar:
            print(tiempoActual - self.ultimoDibujo, self.tiempoDibujar)
            return

        logger.info(f"Deck[Dibujar] {self.nombre}")
        for i in range(self.cantidadBotones):
            key_desface = i + self.baseTeclas + self.desfaceTeclas

            dibujar = list(filter(lambda accion: accion["key"] == key_desface, self.listaAcciones))
            # TODO: Cargar primer los Gifs # if AccionAcual is not None:

            if dibujar:
                accionAcual = dibujar[0]

                if accionAcual.get("imagen"):
                    rutaImagenAcutal = accionAcual.get("imagen")
                    if rutaImagenAcutal == self.archivoImagen[i]:
                        continue
                    self.archivoImagen[i] = rutaImagenAcutal

                DirecionImagen = self.buscarDirecionImagen(accionAcual)
                if DirecionImagen is not None and DirecionImagen.endswith(".gif"):
                    self.DeckGif.ActualizarGif(i, accionAcual, self.folderActual)
                else:
                    self.actualizarIconoBoton(i, accionAcual)

    def limpiarIconos(self):
        """Borra iconos de todo los botones de StreamDeck."""
        if self.conectado:
            logger.info(f"Limpiando {self.nombre}")
            self.DeckGif.Limpiar()
            for i in range(self.cantidadBotones):
                LimpiarIcono(self.deck, i)
            self.archivoImagen = None

    def Brillo(self, Brillo):
        """Cambia brillo de StreamDeck."""
        if self.conectado:
            self.deck.set_brightness(Brillo)

    def CambiarFolder(self, Folder):
        logger.debug(f"Entrando a {Folder}")
        self.folderActual = Folder
        self.ultimoDibujo = -self.tiempoDibujar

    def actualizarBoton(self, Deck, Key, Estado):
        numeroTecla = Key + self.baseTeclas + self.desfaceTeclas
        if Estado:
            self.buscarAccion(numeroTecla, self.estadoTecla.PRESIONADA)
        else:
            self.buscarAccion(numeroTecla, self.estadoTecla.LIBERADA)

    def desconectar(self):
        if self.conectado:
            logger.info(f"Deck[Desconectando] - {self.nombre}")
            self.DeckGif.Desconectar()
            self.conectado = False
            self.deck.reset()
            self.deck.close()

    def __str__(self):
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

        DirecionImagen = self.buscarDirecionImagen(accion)

        if DirecionImagen is not None:
            modificado = True
            if DirecionImagen.endswith(".gif"):
                # TODO: Meter proceso gif adentro
                return None

        self.ponerImagen(imagen, DirecionImagen, accion)

        TextoCargar = accion.get("cargar_titulo")
        if TextoCargar is not None:
            archivoTexto = TextoCargar.get("archivo")
            atributoTexto = TextoCargar.get("atributo")
            if archivoTexto is not None and atributoTexto is not None:
                accion["titulo"] = ObtenerValor(archivoTexto, atributoTexto)

        if "titulo" in accion:
            modificado = True
            self.PonerTexto(imagen, accion, DirecionImagen)

        # if not modificado:
        #     copiaAccion = accion.copy()
        #     copiaAccion["titulo"] = copiaAccion.get("nombre")
        #     self.PonerTexto(imagen, copiaAccion, cortePalabra=True)

        return imagen

    def calcularRutaImagen(self, rutaImagen: str) -> str:

        folderPerfil = self._folderConfigPerfil()
        folderActual = Path(self.folderActual)

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

    def PonerTexto(self, Imagen, accion: dict, DirecionImagen=None, cortePalabra: bool = False):
        """Agrega Texto a Botones de StreamDeck."""
        Titulo: str = str(accion.get("titulo"))
        Lineas = Titulo.split("\\n")
        Titulo = "\n".join(Lineas)
        if cortePalabra:
            Lineas = Titulo.split(" ")
            Titulo = "\n".join(Lineas)
        Titulo_Color = "white"
        Tamanno: int = 40
        Ajustar: bool = True
        Alinear: str = "centro"
        Borde_Color: str = "black"
        Borde_Grosor: int = 5
        if DirecionImagen is not None:
            Alinear = "abajo"
            Tamanno = 20

        dibujo: ImageDraw = ImageDraw.Draw(Imagen)

        if "titulo_opciones" in accion:
            opciones = accion["titulo_opciones"]
            if "tamanno" in opciones:
                Tamanno = opciones["tamanno"]
            if "alinear" in opciones:
                Alinear = opciones["alinear"]
            if "color" in opciones:
                Titulo_Color = opciones["color"]
            if "borde_color" in opciones:
                Borde_Color = opciones["borde_color"]
            if "borde_grosor" in opciones:
                Borde_Grosor = opciones["borde_grosor"]
            if "ajustar" in opciones:
                Ajustar = opciones["ajustar"]

        # TODO: buscar como calcular tamaño de fuente de manera mas eficiente
        while Ajustar:
            fuente = ImageFont.truetype(self.archivoFuente, Tamanno)
            cajaTexto = dibujo.textbbox([0, 0], Titulo, font=fuente)
            Titulo_ancho = cajaTexto[2] - cajaTexto[0]
            Titulo_alto = cajaTexto[3] - cajaTexto[1]

            if Titulo_ancho < Imagen.width:
                break
            # TODO: reducir tamaño si el alto es demasiado
            Tamanno -= 1

        Horizontal = (Imagen.width - Titulo_ancho) / 2

        if Alinear == "centro":
            Vertical = (Imagen.height - Titulo_alto - Tamanno / 2) / 2
        elif Alinear == "ariba":
            Vertical = 0
        else:
            Vertical = Imagen.height - Titulo_alto - Titulo_alto / 3
        PosicionTexto = (Horizontal, Vertical)

        dibujo.text(PosicionTexto, text=Titulo, font=fuente, fill=Titulo_Color, stroke_width=Borde_Grosor, stroke_fill=Borde_Color, align="center")

    def buscarDirecionImagen(self, accion):

        if "imagen_estado" in accion:
            ImagenEstado = accion["imagen_estado"]
            NombreAccion = accion["accion"]
            opcionesAccion = None
            if "opciones" in accion:
                opcionesAccion = accion["opciones"]

            if NombreAccion.startswith("obs"):
                EstadoImagen = self.BuscarImagenOBS(NombreAccion, opcionesAccion)
                if EstadoImagen:
                    DirecionImagen = ImagenEstado["imagen_true"]
                else:
                    DirecionImagen = ImagenEstado["imagen_false"]

                return DirecionImagen

        if "imagen" in accion:
            DirecionImagen = accion["imagen"]
            return DirecionImagen
        elif "accion" in accion:
            NombreAccion = accion["accion"]
            if NombreAccion in self.imagenesBase:
                return self.imagenesBase[NombreAccion]

        return None

    def BuscarImagenOBS(self, NombreAccion, opcionesAccion):
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
