import os
import logging

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import ObtenerConfig, ObtenerValor, UnirPath, RelativoAbsoluto

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

    if 'icono_texto' in accion:
        Texto = ObtenerValor(accion['icono_texto']['archivo'], accion['icono_texto']['atributo'])
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
            EstadoArchivo = ObtenerValor("data/estado.json", accion['nombre'], Depurar=False)
            if EstadoArchivo is not None:
                accion['estado'] = EstadoArchivo

            if accion['estado']:
                NombreIcono = accion['icono_true']
            else:
                NombreIcono = accion['icono_false']

        if 'solo_titulo' in accion and 'titulo' in accion:
            pass
        else:
            PonerImagen(ImagenBoton, NombreIcono, accion, Deck.Folder)

    if 'titulo' in accion:
        PonerTexto(ImagenBoton, accion['titulo'], accion)

    Deck.set_key_image(indice, PILHelper.to_native_format(Deck, ImagenBoton))


def PonerImagen(Imagen, NombreIcono, accion, Folder):
    NombreIcono = RelativoAbsoluto(NombreIcono, Folder)
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
    """Agrega Texto a Botones de StreamDeck."""
    Texto = str(Texto)
    Tamanno = 20
    dibujo = ImageDraw.Draw(Imagen)

    if 'solo_titulo' in accion:
        Tamanno = 40
        centrar = True

    if 'titulo_color' in accion:
        Color = accion['titulo_color']
    else:
        Color = "white"

    # TODO: hacer funcion
    while True:
        fuente = ImageFont.truetype(FuenteIcono, Tamanno)
        Titulo_ancho, Titulo_alto = dibujo.textsize(Texto, font=fuente)
        if Titulo_ancho < Imagen.width:
            break
        Tamanno -= 1

    if centrar:
        PosicionTexto = ((Imagen.width - Titulo_ancho) // 2, (Imagen.height - Titulo_alto - Tamanno/2) // 2)
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
        EsenaActual = ObtenerValor("data/obs.json", "esena_actual", Depurar=False)
        if accion['esena'] == EsenaActual:
            accion['estado'] = True
        else:
            accion['estado'] = False
    elif opcion == 'fuente':
        EstadoFuente = ObtenerValor("data/fuente_obs.json", accion['fuente'], Depurar=False)
        if EstadoFuente is not None:
            accion['estado'] = EstadoFuente
        else:
            accion['estado'] = False
    elif opcion == 'filtro':
        Data = list()
        Data.append(accion['fuente'])
        Data.append(accion['filtro'])
        EstadoFiltro = ObtenerValor("data/filtro_obs.json", Data, Depurar=False)
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
    Estado = ObtenerValor("data/obs.json", atributo, Depurar=False)
    if Estado:
        accion['estado'] = True
    else:
        accion['estado'] = False
