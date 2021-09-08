from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from MiLibrerias import ObtenerFolderConfig, UnirPath


def PonerTexto(Imagen, accion, DirecionImagen=None):
    """Agrega Texto a Botones de StreamDeck."""
    Titulo = str(accion['titulo'])
    Titulo_Color = "white"
    Tamanno = 40
    Alinear = "centro"
    Borde_Color = 'black'
    Borde_Grosor = 5
    if DirecionImagen is not None:
        Alinear = "abajo"
        Tamanno = 20

    dibujo = ImageDraw.Draw(Imagen)

    if 'titulo_opciones' in accion:
        Opciones = accion['titulo_opciones']
        if 'tamanno' in Opciones:
            Tamanno = Opciones['tamanno']
        if 'alinear' in Opciones:
            Alinear = Opciones['alinear']
        if 'color' in Opciones:
            Titulo_Color = Opciones['color']
        if 'borde_color' in Opciones:
            Borde_Color = Opciones['borde_color']
        if 'borde_grosor' in Opciones:
            Borde_Grosor = Opciones['borde_grosor']

    # TODO: hacer funcion mas limpia
    while True:
        fuente = ImageFont.truetype(FuenteIcono, Tamanno)
        Titulo_ancho, Titulo_alto = dibujo.textsize(Titulo, font=fuente)
        if Titulo_ancho < Imagen.width:
            break
        Tamanno -= 1

    Horizontal = (Imagen.width - Titulo_ancho) // 2

    if Alinear == "centro":
        Vertical = (Imagen.height - Titulo_alto - Tamanno/2) // 2
    elif Alinear == "ariba":
        Vertical = 0
    else:
        Vertical = Imagen.height - Titulo_alto - 2
    PosicionTexto = (Horizontal, Vertical)

    dibujo.text(PosicionTexto, text=Titulo, font=fuente,
                fill=Titulo_Color, stroke_width=Borde_Grosor, stroke_fill=Borde_Color)


def PonerFondo(Imagen, accion):
    if "imagen_opciones" in accion:
        Opciones = accion['imagen_opciones']
        if 'fondo' in Opciones:
            ColorFondo = Opciones['fondo']
            dibujo = ImageDraw.Draw(Imagen)
            Tamanno = [(0, 0), (Imagen.width, Imagen.height)]
            dibujo.rectangle(Tamanno, fill=ColorFondo)


def DefinirFuente(Fuente):
    """Definir Fuente para StreanDeck"""
    global FuenteIcono
    FuenteIcono = UnirPath(ObtenerFolderConfig(), Fuente)
