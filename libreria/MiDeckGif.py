import threading
import itertools
import time
import os

from PIL import Image, ImageSequence
from StreamDeck.ImageHelpers import PILHelper
from fractions import Fraction

from MiLibrerias import ConfigurarLogging
from MiLibrerias import ObtenerValor, UnirPath, ObtenerFolderConfig, RelativoAbsoluto

logger = ConfigurarLogging(__name__)

# TODO: Cargar Gif en hilo aparte para no para procesos


class DeckGif(threading.Thread):
    """Clase de Gif para StreamDeck."""

    def __init__(self, Deck):
        """Carga Configuraciones para usar gif."""
        self.Deck = Deck
        self.lock = threading.RLock()
        self.ListaGif = []
        self.EsperaGif = Fraction(1, ObtenerValor(
            "data/streamdeck.json", "gif_fps"))
        self.SiquienteFrame = Fraction(time.monotonic())
        super(DeckGif, self).__init__()

    def run(self):
        """Dibuja un frame de cada gif y espera a siquiente frame."""
        while True:
            # if self.Deck.connected():
            with self.lock:
                for Gif in self.ListaGif:
                    if 'gif_cargado' in Gif:
                        self.DibujarGif(Gif)
                self.SiquienteFrame += self.EsperaGif
                TiempoEspera = float(self.SiquienteFrame) - time.monotonic()
                if TiempoEspera >= 0:
                    time.sleep(TiempoEspera)

    def DibujarGif(self, accion):
        """Dibuja el siquiente frame de gif en StreamDeck."""
        self.Deck.set_key_image(accion['indice'], next(accion['gif_cargado']))

    def Limpiar(self):
        """Borra lista de gif actuales."""
        self.ListaGif = []

    def ActualizarGif(self, indice, accion):
        """Carga los frame si no estas precargado y lo agrega a lista actual gifs."""
        if 'gif_cargado' not in accion:
            accion['indice'] = indice
            self.CargarGif(accion)

        Encontrado = list(filter(lambda Gif: Gif['nombre'] == accion['nombre'], self.ListaGif))
        if not Encontrado:
            self.ListaGif.append(accion)

    def CargarGif(self, accion):
        """Extra frame de un gif y los guarda en una lista."""
        # TODO: agregar titulo a gif
        Gif = list()
        if 'imagen' in accion:
            DirecionGif = accion['imagen']
        elif 'gif' in accion:
            DirecionGif = accion['gif']
        else:
            return

        if not DirecionGif.endswith('gif'):
            return

        DirecionGif = RelativoAbsoluto(DirecionGif, self.Deck.Folder)
        DirecionGif = UnirPath(ObtenerFolderConfig(), DirecionGif)
        if os.path.exists(DirecionGif):
            GifArchivo = Image.open(DirecionGif)
            for frame in ImageSequence.Iterator(GifArchivo):
                Gif_frame = PILHelper.create_scaled_image(self.Deck, frame)
                ImagenNativa = PILHelper.to_native_format(self.Deck, Gif_frame)
                Gif.append(ImagenNativa)
            accion['gif_cargado'] = itertools.cycle(Gif)
        else:
            logger.warning(f"No existe el gif {DirecionGif}")
