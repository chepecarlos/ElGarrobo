import os

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from MiLibrerias import ObtenerFolderConfig, ObtenerValor, UnirPath, RelativoAbsoluto
from MiLibrerias import ObtenerArchivo

from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def ActualizarIcono(Deck, indice, accion):
    global FuenteIcono
    global ImagenBase
    global ListaImagenes

    ImagenBoton = PILHelper.create_image(Deck)

    DirecionImagen = ListaImagenes['base']

    if 'imagen' in accion:
        DirecionImagen = accion['imagen']
        if DirecionImagen.endswith(".gif"):
            # TODO: Meter proceso gif adentro
            return
    elif 'accion' in accion:
        NombreAccion = accion['accion']
        if NombreAccion in ListaImagenes:
            DirecionImagen = ListaImagenes[NombreAccion]

    if 'gif' in accion:
        return

    if 'obs' in accion:
        ActualizarImagenOBS(accion)

    if 'icono_texto' in accion:
        Texto = ObtenerValor(
            accion['icono_texto']['archivo'], accion['icono_texto']['atributo'])
        PonerTexto(ImagenBoton, Texto, accion, True)
    else:
        # DirecionImagen = ImagenBase['base']

        if 'icono' in accion:
            DirecionImagen = accion['icono']
        elif 'opcion' in accion:
            if accion['opcion'] == 'regresar':
                DirecionImagen = ImagenBase['regresar']
            elif accion['opcion'] == 'siquiente':
                DirecionImagen = ImagenBase['siquiente']
            elif accion['opcion'] == 'anterior':
                DirecionImagen = ImagenBase['anterior']
        elif 'estado' in accion:
            EstadoArchivo = ObtenerValor("data/estado.json", accion['nombre'])
            if EstadoArchivo is not None:
                accion['estado'] = EstadoArchivo

            if accion['estado']:
                DirecionImagen = accion['icono_true']
            else:
                DirecionImagen = accion['icono_false']

    if not 'solo_titulo' in accion:
        PonerImagen(ImagenBoton, DirecionImagen, accion, Deck.Folder)

    if 'titulo' in accion:
        PonerTexto(ImagenBoton, accion['titulo'], accion)

    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))


def PonerImagen(Imagen, NombreIcono, accion, Folder):
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


def PonerTexto(Imagen, Texto, accion, centrar=False):
    """Agrega Texto a Botones de StreamDeck."""
    Texto = str(Texto)
    Tamanno = 20
    Color = "white"
    Centrado = False
    dibujo = ImageDraw.Draw(Imagen)

    if 'titulo_opciones' in accion:
        Opciones = accion['titulo_opciones']
        if 'color' in Opciones:
            Color = Opciones['color']
        if 'centrado' in Opciones:
            Tamanno = 40
            Centrado = Opciones['centrado']
        if 'tamanno' in Opciones:
            Tamanno = Opciones['tamanno']
        if 'borde' in Opciones:
            Borde = Opciones['borde']

    else:
        if 'solo_titulo' in accion:
            Tamanno = 40
            Centrado = True

        if 'titulo_color' in accion:
            Color = accion['titulo_color']

    # TODO: hacer funcion mas limpia
    while True:
        fuente = ImageFont.truetype(FuenteIcono, Tamanno)
        Titulo_ancho, Titulo_alto = dibujo.textsize(Texto, font=fuente)
        if Titulo_ancho < Imagen.width:
            break
        Tamanno -= 1

    if Centrado:
        PosicionTexto = ((Imagen.width - Titulo_ancho) // 2,
                         (Imagen.height - Titulo_alto - Tamanno/2) // 2)
    else:
        PosicionTexto = ((Imagen.width - Titulo_ancho) //
                         2, Imagen.height - Titulo_alto - 2)

    dibujo.text(PosicionTexto, text=Texto, font=fuente, fill=Color)


def DefinirFuente(Fuente):
    global FuenteIcono
    FuenteIcono = UnirPath(ObtenerFolderConfig(), Fuente)


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
