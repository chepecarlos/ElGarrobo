import os
import itertools
import time
import threading
import logging

from PIL import Image, ImageDraw, ImageFont, ImageSequence
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError
from fractions import Fraction

from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import ObtenerConfig, UnirPath

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


def ActualizarIcono(Deck, indice, accion):
    global FuenteIcono
    ImagenBoton = PILHelper.create_image(Deck)

    if 'gif' in accion:
        return

    if 'icono' in accion:
        NombreIcono = accion['icono']

        PonerImagen(ImagenBoton, NombreIcono, accion)

    if 'titulo' in accion:
        PonerTexto(ImagenBoton, accion['titulo'], accion)

    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))


def PonerImagen(Imagen, NombreIcono, accion):
    DirecionIcono = UnirPath(ObtenerConfig(), NombreIcono)
    if os.path.exists(DirecionIcono):
        Icono = Image.open(DirecionIcono).convert("RGBA")
        if 'titulo' in accion:
            Icono.thumbnail((Imagen.width, Imagen.height - 20), Image.LANCZOS)
        else:
            Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)
    else:
        logging.warning(f"No se encontr icono {DirecionIcono}")
        Icono = Image.new(mode="RGBA", size=(256, 256), color=(153, 153, 255))
        Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)

    IconoPosicion = ((Imagen.width - Icono.width) // 2, 0)
    Imagen.paste(Icono, IconoPosicion, Icono)


def PonerTexto(Imagen, Texto, accion):
    Tamanno = 20
    dibujo = ImageDraw.Draw(Imagen)

    if 'titulo_color' in accion:
        Color = accion['titulo_color']
    else:
        Color = "white"

    while True:
        fuente = ImageFont.truetype(FuenteIcono, Tamanno)
        Titulo_ancho, Titulo_alto = dibujo.textsize(Texto, font=fuente)
        if Titulo_ancho < Imagen.width:
            break
        Tamanno -= 1
    PosicionTexto = ((Imagen.width - Titulo_ancho) // 2, Imagen.height - Titulo_alto - 2)
    dibujo.text(PosicionTexto, text=Texto, font=fuente, fill=Color)


def DefinirFuente(Fuente):
    global FuenteIcono
    FuenteIcono = UnirPath(ObtenerConfig(), Fuente)
