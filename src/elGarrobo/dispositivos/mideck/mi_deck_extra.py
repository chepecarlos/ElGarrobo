from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerArchivo, ObtenerFolderConfig, ObtenerValor, UnirPath
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

logger = ConfigurarLogging(__name__)


def PonerTexto(Imagen, accion, DirecionImagen=None):
    """Agrega Texto a Botones de StreamDeck."""
    Titulo = str(accion["titulo"])
    Titulo_Color = "white"
    Tamanno = 40
    Ajustar = True
    Alinear = "centro"
    Borde_Color = "black"
    Borde_Grosor = 5
    if DirecionImagen is not None:
        Alinear = "abajo"
        Tamanno = 20

    dibujo = ImageDraw.Draw(Imagen)

    if "titulo_opciones" in accion:
        opciones = accion["titulo_opciones"]
        if "tamanno" in opciones:
            Tamanno = opciones["tamanno"]
        if "alinear" in opciones:
            Alinear = opciones["alinear"]
        if "color" in opciones:
            Titulo_Color = opciones["color"]
        if "borde_color" in opciones:
            Borde_Color = opciones["borde_color"]
        if "borde_grosor" in opciones:
            Borde_Grosor = opciones["borde_grosor"]
        if "ajustar" in opciones:
            Ajustar = opciones["ajustar"]

    # TODO: hacer funcion mas limpia
    while Ajustar:
        fuente = ImageFont.truetype(FuenteIcono, Tamanno)
        Titulo_ancho, Titulo_alto = dibujo.textsize(Titulo, font=fuente)
        if Titulo_ancho < Imagen.width:
            break
        Tamanno -= 1

    Horizontal = (Imagen.width - Titulo_ancho) // 2

    if Alinear == "centro":
        Vertical = (Imagen.height - Titulo_alto - Tamanno / 2) // 2
    elif Alinear == "ariba":
        Vertical = 0
    else:
        Vertical = Imagen.height - Titulo_alto - 2
    PosicionTexto = (Horizontal, Vertical)

    dibujo.text(
        PosicionTexto, text=Titulo, font=fuente, fill=Titulo_Color, stroke_width=Borde_Grosor, stroke_fill=Borde_Color
    )


def PonerFondo(Imagen, accion):
    if "imagen_opciones" in accion:
        opciones = accion["imagen_opciones"]
        if "fondo" in opciones:
            ColorFondo = opciones["fondo"]
            dibujo = ImageDraw.Draw(Imagen)
            Tamanno = [(0, 0), (Imagen.width, Imagen.height)]
            dibujo.rectangle(Tamanno, fill=ColorFondo)


def DefinirFuente(Fuente):
    """Definir Fuente para StreanDeck"""
    global FuenteIcono
    FuenteIcono = UnirPath(ObtenerFolderConfig(), Fuente)


def BuscarDirecionImagen(accion):

    if "imagen_estado" in accion:
        ImagenEstado = accion["imagen_estado"]
        NombreAccion = accion["accion"]
        opcionesAccion = None
        if "opciones" in accion:
            opcionesAccion = accion["opciones"]

        if NombreAccion.startswith("obs"):
            EstadoImagen = BuscarImagenOBS(NombreAccion, opcionesAccion)
            if EstadoImagen:
                DirecionImagen = ImagenEstado["imagen_true"]
            else:
                DirecionImagen = ImagenEstado["imagen_false"]

            return DirecionImagen

    if "imagen" in accion:
        DirecionImagen = accion["imagen"]
        return DirecionImagen
    elif "accion" in accion:
        NombreAccion = accion["accion"]
        if NombreAccion in ListaImagenes:
            return ListaImagenes[NombreAccion]

    return None


def BuscarImagenOBS(NombreAccion, opcionesAccion):
    Estado = None

    ListaBasicas = [
        "obs_conectar",
        "obs_grabar",
        "obs_envivo",
        "obs_camara_virtual"
    ]
    for Basica in ListaBasicas:
        if NombreAccion == Basica:
            Estado = ObtenerValor("data/obs.json", Basica)

    if NombreAccion == "obs_escena":
        if "escena" in opcionesAccion:
            EscenaActual = opcionesAccion["escena"]
            EscenaActiva = ObtenerValor("data/obs.json", "obs_escena")
            if EscenaActual == EscenaActiva:
                Estado = True
            else:
                Estado = False
    elif NombreAccion == "obs_fuente":
        if "fuente" in opcionesAccion:
            FuenteActual = opcionesAccion["fuente"]
            Estado = ObtenerValor("data/obs_fuente.json", FuenteActual)
    elif NombreAccion == "obs_filtro":
        if "fuente" in opcionesAccion:
            Fuente = opcionesAccion["fuente"]
        if "filtro" in opcionesAccion:
            Filtro = opcionesAccion["filtro"]
        if Fuente is not None and Filtro is not None:
            Estado = ObtenerValor("data/obs_filtro.json", [Fuente, Filtro])

    if Estado is None:
        Estado = False

    return Estado


def DefinirImagenes():
    global ListaImagenes
    ListaImagenes = ObtenerArchivo("imagenes_base.json")
