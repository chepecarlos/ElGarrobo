import threading
import itertools
import time
import os

from PIL import Image, ImageDraw, ImageFont, ImageSequence
from StreamDeck.ImageHelpers import PILHelper
from fractions import Fraction

from .mi_deck_extra import PonerTexto, BuscarDirecionImagen

from MiLibrerias import ConfigurarLogging
from MiLibrerias import ObtenerValor, UnirPath, ObtenerFolderConfig, RelativoAbsoluto

logger = ConfigurarLogging(__name__)

# TODO: Cargar Gif en hilo aparte para no para procesos


class DeckGif(threading.Thread):
    """Clase de Gif para StreamDeck."""

    def __init__(self, Deck):
        """Carga Configuraciones para usar gif."""
        self.Deck = Deck
        # self.lock = threading.RLock()
        self.ListaGif = []
        self.ListaGifCargar = []
        self.Activo = True
        self.EsperaGif = Fraction(1, ObtenerValor("data/streamdeck.json", "gif_fps"))
        self.SiquienteFrame = Fraction(time.monotonic())
        super(DeckGif, self).__init__()

    def run(self):
        """Dibuja un frame de cada gif y espera a siquiente frame."""
        while self.Activo:
            # if self.Deck.connected():
            # with self.lock:
            try:
                if self.ListaGifCargar:
                    Gif = self.ListaGifCargar[0]
                    # for Gif in self.ListaGifCargar:
                    self.CargarGif(Gif)
                    self.ListaGifCargar = self.ListaGifCargar[1:]
                    # self.ListaGifCargar = []

                for Gif in self.ListaGif:
                    if "gif_cargado" in Gif:
                        self.DibujarGif(Gif)
                self.SiquienteFrame += self.EsperaGif
                TiempoEspera = float(self.SiquienteFrame) - time.monotonic()
                if TiempoEspera >= 0:
                    time.sleep(TiempoEspera)
            except Exception as error:
                logger.exception(f"Gif[Error] {error} {self.Activo}")
                self.Activo = False

    def DibujarGif(self, accion):
        """Dibuja el siquiente frame de gif en StreamDeck."""
        if self.Activo:
            self.Deck.set_key_image(accion["indice"], next(accion["gif_cargado"]))

    def Limpiar(self):
        """Borra lista de gif actuales."""
        self.ListaGif = []
        self.ListaGifCargar = []

    def ActualizarGif(self, indice, accion):
        """Carga los frame si no estas precargado y lo agrega a lista actual gifs."""

        Encontrado = list(filter(lambda Gif: Gif["nombre"] == accion["nombre"], self.ListaGif))
        if not Encontrado:
            accion["indice"] = indice
            self.ListaGifCargar.append(accion)

    def CargarGif(self, accion):
        """Extra frame de un gif y los guarda en una lista."""
        # TODO: Errro con git con estado no se desactiva
        if "gif_cargado" in accion:
            self.ListaGif.append(accion)
            return

        DirecionGif = BuscarDirecionImagen(accion)

        if DirecionGif is not None and not DirecionGif.endswith("gif"):
            return

        Gif = list()
        ColorFondo = "black"
        if "imagen_opciones" in accion:
            Opciones = accion["imagen_opciones"]
            if "fondo" in Opciones:
                ColorFondo = Opciones["fondo"]

        DirecionGif = RelativoAbsoluto(DirecionGif, self.Deck.Folder)
        DirecionGif = UnirPath(ObtenerFolderConfig(), DirecionGif)
        if os.path.exists(DirecionGif):
            GifArchivo = Image.open(DirecionGif)
            for frame in ImageSequence.Iterator(GifArchivo):
                Gif_frame = PILHelper.create_scaled_image(self.Deck, frame, background=ColorFondo)

                if "cargar_titulo" in accion:
                    TextoCargar = accion["cargar_titulo"]
                    if "archivo" in TextoCargar and "atributo" in TextoCargar:
                        accion["titulo"] = ObtenerValor(TextoCargar["archivo"], TextoCargar["atributo"])

                if "titulo" in accion:
                    PonerTexto(Gif_frame, accion, True)
                ImagenNativa = PILHelper.to_native_format(self.Deck, Gif_frame)

                Gif.append(ImagenNativa)
            accion["gif_cargado"] = itertools.cycle(Gif)
            self.ListaGif.append(accion)
        else:
            logger.warning(f"Deck[No Gifs] {DirecionGif}")

    def Desconectar(self):
        self.Limpiar()
        self.Activo = False
