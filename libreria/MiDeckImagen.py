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
from libreria.FuncionesArchivos import ObtenerConfig, ObtenerValor, UnirPath

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


def ActualizarIcono(Deck, indice, accion):
    global FuenteIcono
    global ImagenBase
    ImagenBoton = PILHelper.create_image(Deck)

    if 'gif' in accion:
        return

    if 'obs' in accion:
        ActualizarImagenOBS(accion)

    if 'texto' in accion:
        Texto = ObtenerValor(accion['texto']['archivo'], accion['texto']['atributo'])
        PonerTexto(ImagenBoton, Texto, accion, True)
    else:
        NombreIcono = ImagenBase['base']

        if 'icono' in accion:
            NombreIcono = accion['icono']
        elif 'opcion' in accion:
            if accion['opcion'] == 'regresar':
                NombreIcono = ImagenBase['regresar']
            elif accion['opcion'] == 'siquiente':
                NombreIcono = ImagenBase['siquiente']
            elif accion['opcion'] == 'anterior':
                NombreIcono = ImagenBase['anterior']
        elif 'estado' in accion:
            if accion['estado']:
                NombreIcono = accion['icono_true']
            else:
                NombreIcono = accion['icono_false']

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


def PonerTexto(Imagen, Texto, accion, centrar=False):
    Texto = str(Texto)
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

    if centrar:
        PosicionTexto = ((Imagen.width - Titulo_ancho) // 2, (Imagen.height - Titulo_alto - 20) // 2)
    else:
        PosicionTexto = ((Imagen.width - Titulo_ancho) // 2, Imagen.height - Titulo_alto - 2)

    dibujo.text(PosicionTexto, text=Texto, font=fuente, fill=Color)


def DefinirFuente(Fuente):
    global FuenteIcono
    FuenteIcono = UnirPath(ObtenerConfig(), Fuente)


def DefinirImagenes(Data):
    global ImagenBase
    ImagenBase = Data


def LimpiarIcono(Deck, indice):
    ImagenBoton = PILHelper.create_image(Deck)
    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))


def ActualizarImagenOBS(accion):
    opcion = accion['obs']
    if opcion == 'esena':
        EsenaActual = ObtenerValor("data/obs.json", "esena_actual")
        if accion['esena'] == EsenaActual:
            accion['estado'] = True
        else:
            accion['estado'] = False
    elif opcion == 'fuente':
        EstadoFuente = ObtenerValor("data/fuente_obs.json", accion['fuente'])
        if EstadoFuente is not None:
            accion['estado'] = EstadoFuente
        else:
            accion['estado'] = False
    elif opcion == 'filtro':
        Data = list()
        Data.append(accion['fuente'])
        Data.append(accion['filtro'])
        EstadoFiltro = ObtenerValor("data/filtro_obs.json", Data)
        if EstadoFiltro is not None:
            accion['estado'] = EstadoFiltro
        else:
            accion['estado'] = False
    elif opcion == 'grabando':
        ActualizarEstado(accion, "grabando")
    elif opcion == 'envivo':
        ActualizarEstado(accion, "envivo")
    elif opcion == 'conectar':
        ActualizarEstado(accion, "conectado")


def ActualizarEstado(accion, atributo):
    Estado = ObtenerValor("data/obs.json", atributo)
    if Estado:
        accion['estado'] = True
    else:
        accion['estado'] = False
