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
    ImagenBoton = PILHelper.create_image(Deck)
    logger.info(f"Loger {indice} - {accion}")

    if 'gif' in accion:
        return

    if 'titulo' in accion:
        TituloBoton = accion['titulo']
    else:
        TituloBoton = ''

    if 'icono' in accion:
        NombreIcono = accion['icono']

    if 'titulo_color' in accion:
        ColorTexto = accion['titulo_color']
    else:
        ColorTexto = "white"

    DirecionIcono = UnirPath(ObtenerConfig(), NombreIcono)
    if os.path.exists(DirecionIcono):
        Icono = Image.open(DirecionIcono).convert("RGBA")
        if TituloBoton:
            Icono.thumbnail((ImagenBoton.width, ImagenBoton.height - 20), Image.LANCZOS)
        else:
            Icono.thumbnail((ImagenBoton.width, ImagenBoton.height), Image.LANCZOS)
        pass
    else:
        logging.warning(f"No se encontr icono {DirecionIcono}")
        Icono = Image.new(mode="RGBA", size=(256, 256), color=(153, 153, 255))
        Icono.thumbnail((ImagenBoton.width, ImagenBoton.height), Image.LANCZOS)

    IconoPosicion = ((ImagenBoton.width - Icono.width) // 2, 0)
    ImagenBoton.paste(Icono, IconoPosicion, Icono)

    if TituloBoton:
        dibujo = ImageDraw.Draw(ImagenBoton)
        font = ImageFont.truetype(FuenteIcono, 14)
        label_w, label_h = dibujo.textsize(TituloBoton, font=font)
        label_pos = ((ImagenBoton.width - label_w) // 2, ImagenBoton.height - 20)
        dibujo.text(label_pos, text=TituloBoton, font=font, fill=ColorTexto)

    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))


def DefinirFuente(Fuente):
    global FuenteIcono
    FuenteIcono = UnirPath(ObtenerConfig(), Fuente)
