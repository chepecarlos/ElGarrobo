import threading
import itertools
import time
import os
import logging

from PIL import Image, ImageSequence
from StreamDeck.ImageHelpers import PILHelper
from fractions import Fraction

from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import ObtenerValor, UnirPath, ObtenerConfig

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class DeckGif(threading.Thread):

    def __init__(self, Deck):
        self.Deck = Deck
        self.lock = threading.RLock()
        self.ListaGif = []
        self.EsperaGif = Fraction(1, ObtenerValor("data/streandeck.json", "gif_fps"))
        self.SiquienteFrame = Fraction(time.monotonic())
        super(DeckGif, self).__init__()

    def run(self):
        while True:
            with self.lock:
                for Gif in self.ListaGif:
                    if 'git_cargado' in Gif:
                        self.DibujarGif(Gif)
                self.SiquienteFrame += self.EsperaGif
                TiempoEspera = float(self.SiquienteFrame) - time.monotonic()
                if TiempoEspera >= 0:
                    time.sleep(TiempoEspera)

    def Limpiar(self):
        self.ListaGif = []

    def LimpiarGif(self, i):
        pass

    def DibujarGif(self, accion):
        self.Deck.set_key_image(accion['indice'], next(accion['git_cargado']))

    def ActualizarGif(self, indice, accion):
        if not('gif_cargado' in accion):
            accion['indice'] = indice
            self.CargarGif(accion)
        self.ListaGif.append(accion)

    def CargarGif(self, accion):
        # TODO agregar titulo a git
        Gif = list()
        GitPath = accion['gif']
        GitPath = UnirPath(ObtenerConfig(), GitPath)
        if os.path.exists(GitPath):
            GifArchivo = Image.open(GitPath)
            for frame in ImageSequence.Iterator(GifArchivo):
                Gif_frame = PILHelper.create_scaled_image(self.Deck, frame)
                ImagenNativa = PILHelper.to_native_format(self.Deck, Gif_frame)
                Gif.append(ImagenNativa)
            accion['git_cargado'] = itertools.cycle(Gif)
        else:
            logger.warning(f"No existe el gif {GitPath}")
