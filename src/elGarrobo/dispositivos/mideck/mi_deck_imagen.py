import os

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from elGarrobo.miLibrerias import (
    ConfigurarLogging,
    ObtenerArchivo,
    ObtenerFolderConfig,
    ObtenerValor,
    RelativoAbsoluto,
    UnirPath,
)

from .mi_deck_extra import BuscarDirecionImagen, PonerTexto

logger = ConfigurarLogging(__name__)


def ActualizarIcono(Deck, indice, accion):
    global FuenteIcono
    global ImagenBase
    global ListaImagenes

    ColorFondo = "black"
    imagenFondo = None

    if "imagen_opciones" in accion:
        opciones = accion["imagen_opciones"]
        if "fondo" in opciones:
            ColorFondo = opciones["fondo"]
        if "imagen" in opciones:
            imagenFondo = opciones["imagen"]

    ImagenBoton = PILHelper.create_image(Deck, background=ColorFondo)

    if imagenFondo is not None:
        PonerImagen(ImagenBoton, imagenFondo, accion, Deck.Folder, True)

    DirecionImagen = BuscarDirecionImagen(accion)

    if DirecionImagen is not None:
        if DirecionImagen.endswith(".gif"):
            # TODO: Meter proceso gif adentro
            return None

    PonerImagen(ImagenBoton, DirecionImagen, accion, Deck.Folder)

    TextoCargar = accion.get("cargar_titulo")
    if TextoCargar is not None:
        archivoTexto = TextoCargar.get("archivo")
        atributoTexto = TextoCargar.get("atributo")
        if archivoTexto is not None and atributoTexto is not None:
            accion["titulo"] = ObtenerValor(archivoTexto, atributoTexto)

    if "titulo" in accion:
        PonerTexto(ImagenBoton, accion, DirecionImagen)

    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))


def PonerImagen(Imagen, NombreIcono, accion, Folder, fondo=False):
    if NombreIcono is None:
        return
    NombreIcono = RelativoAbsoluto(NombreIcono, Folder)
    DirecionIcono = UnirPath(ObtenerFolderConfig(), NombreIcono)

    if os.path.exists(DirecionIcono):
        Icono = Image.open(DirecionIcono).convert("RGBA")
        if "titulo" in accion and not fondo:
            Icono.thumbnail((Imagen.width, Imagen.height - 20), Image.LANCZOS)
        else:
            Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)
    else:
        logger.warning(f"Deck[No Imagen] {NombreIcono}")
        Icono = Image.new(mode="RGBA", size=(256, 256), color=(153, 153, 255))
        Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)

    IconoPosicion = ((Imagen.width - Icono.width) // 2, 0)
    Imagen.paste(Icono, IconoPosicion, Icono)


def LimpiarIcono(Deck, indice):
    ImagenBoton = PILHelper.create_image(Deck)
    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))
