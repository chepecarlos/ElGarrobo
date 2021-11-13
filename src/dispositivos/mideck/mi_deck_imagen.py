import os

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from .mi_deck_extra import PonerTexto, BuscarDirecionImagen

from MiLibrerias import ObtenerFolderConfig, ObtenerValor, UnirPath, RelativoAbsoluto
from MiLibrerias import ObtenerArchivo

from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def ActualizarIcono(Deck, indice, accion):
    global FuenteIcono
    global ImagenBase
    global ListaImagenes

    ColorFondo = "black"
    if "imagen_opciones" in accion:
        Opciones = accion["imagen_opciones"]
        if "fondo" in Opciones:
            ColorFondo = Opciones["fondo"]

    ImagenBoton = PILHelper.create_image(Deck, background=ColorFondo)

    DirecionImagen = BuscarDirecionImagen(accion)

    if DirecionImagen is not None:
        if DirecionImagen.endswith(".gif"):
            # TODO: Meter proceso gif adentro
            return None

    PonerImagen(ImagenBoton, DirecionImagen, accion, Deck.Folder)

    if "cargar_texto" in accion:
        TextoCargar = accion["cargar_texto"]
        if 'archivo' in TextoCargar and "atributo" in TextoCargar:
            accion["titulo"] = ObtenerValor(TextoCargar["archivo"], TextoCargar["atributo"])

    if "titulo" in accion:
        PonerTexto(ImagenBoton, accion, DirecionImagen)

    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))


def PonerImagen(Imagen, NombreIcono, accion, Folder):
    if NombreIcono is None:
        return
    NombreIcono = RelativoAbsoluto(NombreIcono, Folder)
    DirecionIcono = UnirPath(ObtenerFolderConfig(), NombreIcono)

    if os.path.exists(DirecionIcono):
        Icono = Image.open(DirecionIcono).convert("RGBA")
        if "titulo" in accion:
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
