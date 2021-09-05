import os

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from .MiDeckExtras import PonerTexto

from MiLibrerias import ObtenerFolderConfig, ObtenerValor, UnirPath, RelativoAbsoluto
from MiLibrerias import ObtenerArchivo

from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def ActualizarIcono(Deck, indice, accion):
    global FuenteIcono
    global ImagenBase
    global ListaImagenes

    ImagenBoton = PILHelper.create_image(Deck)

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

    if 'gif' in accion:
        return None

    if 'obs' in accion:
        ActualizarImagenOBS(accion)

    if 'icono' in accion:
        return accion['icono']
    elif 'opcion' in accion:
        if accion['opcion'] == 'regresar':
            return ImagenBase['regresar']
        elif accion['opcion'] == 'siquiente':
            return ImagenBase['siquiente']
        elif accion['opcion'] == 'anterior':
            return ImagenBase['anterior']
    elif 'estado' in accion:
        EstadoArchivo = ObtenerValor("data/estado.json", accion['nombre'])
        if EstadoArchivo is not None:
            accion['estado'] = EstadoArchivo

        if accion['estado']:
            return accion['icono_true']
        else:
            return accion['icono_false']

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


# def PonerTexto(Imagen,  DirecionImagen, accion):
#     """Agrega Texto a Botones de StreamDeck."""
#     Titulo = str(accion['titulo'])
#     Titulo_Color = "white"
#     Tamanno = 40
#     Alinear = "centro"
#     Borde_Color = 'black'
#     Borde_Grosor = 5
#     if DirecionImagen is not None:
#         Alinear = "abajo"
#         Tamanno = 20

#     dibujo = ImageDraw.Draw(Imagen)

#     if 'titulo_opciones' in accion:
#         Opciones = accion['titulo_opciones']
#         if 'tamanno' in Opciones:
#             Tamanno = Opciones['tamanno']
#         if 'alinear' in Opciones:
#             Alinear = Opciones['alinear']
#         if 'color' in Opciones:
#             Titulo_Color = Opciones['color']
#         if 'borde_color' in Opciones:
#             Borde_Color = Opciones['borde_color']
#         if 'borde_grosor' in Opciones:
#             Borde_Grosor = Opciones['borde_grosor']

#     # TODO: hacer funcion mas limpia
#     while True:
#         fuente = ImageFont.truetype(FuenteIcono, Tamanno)
#         Titulo_ancho, Titulo_alto = dibujo.textsize(Titulo, font=fuente)
#         if Titulo_ancho < Imagen.width:
#             break
#         Tamanno -= 1

#     Horizontal = (Imagen.width - Titulo_ancho) // 2

#     if Alinear == "centro":
#         Vertical = (Imagen.height - Titulo_alto - Tamanno/2) // 2
#     elif Alinear == "ariba":
#         Vertical = 0
#     else:
#         Vertical = Imagen.height - Titulo_alto - 2
#     PosicionTexto = (Horizontal, Vertical)

#     dibujo.text(PosicionTexto, text=Titulo, font=fuente,
#                 fill=Titulo_Color, stroke_width=Borde_Grosor, stroke_fill=Borde_Color)


# def DefinirFuente(Fuente):
#     global FuenteIcono
#     FuenteIcono = UnirPath(ObtenerFolderConfig(), Fuente)


def DefinirImagenes(Data):
    global ListaImagenes
    global ImagenBase
    ImagenBase = Data
    ListaImagenes = ObtenerArchivo("imagenes_base.json")


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
