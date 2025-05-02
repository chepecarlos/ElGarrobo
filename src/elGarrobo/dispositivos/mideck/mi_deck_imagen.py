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


def ActualizarIcono(Deck, indice: int, accion, folder: str):

    colorFondo: str = "black"
    
    opciones = accion.get("imagen_opciones")
    if opciones:
        if "fondo" in opciones:
            colorFondo = opciones["fondo"]

    ImagenDeck: Image = PILHelper.create_image(Deck, background=colorFondo)

    ImagenBoton: Image = ObtenerImagen(ImagenDeck, accion, folder)

    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))


def ObtenerImagen(imagen: Image, accion, folder: str) -> Image:
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
        PonerImagen(imagen, imagenFondo, accion, folder, True)

    DirecionImagen = BuscarDirecionImagen(accion)

    if DirecionImagen is not None:
        modificado = True
        if DirecionImagen.endswith(".gif"):
            # TODO: Meter proceso gif adentro
            return None

    PonerImagen(imagen, DirecionImagen, accion, folder)

    TextoCargar = accion.get("cargar_titulo")
    if TextoCargar is not None:
        archivoTexto = TextoCargar.get("archivo")
        atributoTexto = TextoCargar.get("atributo")
        if archivoTexto is not None and atributoTexto is not None:
            accion["titulo"] = ObtenerValor(archivoTexto, atributoTexto)

    if "titulo" in accion:
        modificado = True
        PonerTexto(imagen, accion, DirecionImagen)

    if not modificado:
        copiaAccion = accion.copy()
        copiaAccion["titulo"] = copiaAccion.get("nombre")
        PonerTexto(imagen, copiaAccion, cortePalabra=True)

    return imagen


def PonerImagen(Imagen: Image, NombreIcono: str, accion, Folder, fondo: bool = False):
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
