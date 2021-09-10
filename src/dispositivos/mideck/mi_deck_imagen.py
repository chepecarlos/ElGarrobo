import os

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from .mi_deck_extra import PonerTexto

from MiLibrerias import ObtenerFolderConfig, ObtenerValor, UnirPath, RelativoAbsoluto
from MiLibrerias import ObtenerArchivo

from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def ActualizarIcono(Deck, indice, accion):
    global FuenteIcono
    global ImagenBase
    global ListaImagenes

    ColorFondo = 'black'
    if "imagen_opciones" in accion:
        Opciones = accion['imagen_opciones']
        if 'fondo' in Opciones:
            ColorFondo = Opciones['fondo']

    ImagenBoton = PILHelper.create_image(Deck, background=ColorFondo)

    DirecionImagen = BuscarDirecionImagen(accion)

    PonerImagen(ImagenBoton, DirecionImagen, accion, Deck.Folder)

    if 'icono_texto' in accion:
        Texto = ObtenerValor(
            accion['icono_texto']['archivo'], accion['icono_texto']['atributo'])
        PonerTexto(ImagenBoton, accion, DirecionImagen)

    if 'titulo' in accion:
        PonerTexto(ImagenBoton, accion, DirecionImagen)

    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))


def BuscarDirecionImagen(accion):

    if 'imagen_estado' in accion:
        ImagenEstado = accion['imagen_estado']
        NombreAccion = accion['accion']
        if 'opciones' in accion:
            OpcionesAccion = accion['opciones']
        else:
            OpcionesAccion = None

        if NombreAccion.startswith('obs'):
            EstadoImagen = BuscarImagenOBS(NombreAccion, OpcionesAccion)
            if EstadoImagen:
                DirecionImagen = ImagenEstado['imagen_true']
            else:
                DirecionImagen = ImagenEstado['imagen_false']

            return DirecionImagen
    if 'imagen' in accion:
        DirecionImagen = accion['imagen']
        if DirecionImagen.endswith(".gif"):
            # TODO: Meter proceso gif adentro
            return None
        return DirecionImagen
    elif 'accion' in accion:
        NombreAccion = accion['accion']
        if NombreAccion in ListaImagenes:
            return ListaImagenes[NombreAccion]

    return None


def PonerImagen(Imagen, NombreIcono, accion, Folder):
    if NombreIcono is None:
        return
    NombreIcono = RelativoAbsoluto(NombreIcono, Folder)
    DirecionIcono = UnirPath(ObtenerFolderConfig(), NombreIcono)

    if os.path.exists(DirecionIcono):
        Icono = Image.open(DirecionIcono).convert("RGBA")
        if 'titulo' in accion:
            Icono.thumbnail((Imagen.width, Imagen.height - 20), Image.LANCZOS)
        else:
            Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)
    else:
        logger.warning(f"No se encontr icono {NombreIcono} {DirecionIcono}")
        Icono = Image.new(mode="RGBA", size=(256, 256), color=(153, 153, 255))
        Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)

    IconoPosicion = ((Imagen.width - Icono.width) // 2, 0)
    Imagen.paste(Icono, IconoPosicion, Icono)


def BuscarImagenOBS(NombreAccion, OpcionesAccion):
    Estado = None

    ListaBasicas = ["obs_conectar", "obs_grabar", "obs_envivo", ]
    for Basica in ListaBasicas:
        if NombreAccion == Basica:
            Estado = ObtenerValor("data/obs.json", Basica)
    
    if NombreAccion == "obs_escena":
        if 'escena' in OpcionesAccion:
            EscenaActual = OpcionesAccion['escena']
            EscenaActiva = ObtenerValor("data/obs.json", "obs_escena")
            if EscenaActual == EscenaActiva:
                Estado = True
            else:
                Estado = False
    elif NombreAccion == 'obs_fuente':
        if 'fuente' in OpcionesAccion:
            FuenteActual = OpcionesAccion['fuente']
            Estado = ObtenerValor("data/obs_fuente.json", FuenteActual)
    elif NombreAccion == 'obs_filtro':
        if 'fuente' in OpcionesAccion:
            Fuente = OpcionesAccion['fuente']
        if 'filtro' in OpcionesAccion:
            Filtro = OpcionesAccion['filtro']
        if Fuente is not None and Filtro is not None:
            Estado = ObtenerValor("data/obs_filtro.json", [Fuente, Filtro])

    if Estado is None:
        Estado = False

    return Estado


def DefinirImagenes(Data):
    global ListaImagenes
    global ImagenBase
    ImagenBase = Data
    ListaImagenes = ObtenerArchivo("imagenes_base.json")


def LimpiarIcono(Deck, indice):
    ImagenBoton = PILHelper.create_image(Deck)
    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))
