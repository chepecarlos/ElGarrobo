import os
import itertools
import time
import threading

from PIL import Image, ImageDraw, ImageFont, ImageSequence
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError
from fractions import Fraction

from Extra.Depuracion import Imprimir
from Extra.FuncionesProyecto import ObtenerDato


def ActualizarIcono(MiDeck, IndiceBoton, Limpiar=False):
    global FuenteBoton

    Deck = MiDeck.Deck
    Data = MiDeck.Data
    BotonActuales = MiDeck.BotonActuales
    DesfaceBoton = MiDeck.DesfaceBoton

    ImagenBoton = PILHelper.create_image(Deck)

    if not Limpiar:
        if(IndiceBoton + DesfaceBoton < 0 or IndiceBoton + DesfaceBoton > Deck.key_count()):
            return

        ActualBoton = BotonActuales[IndiceBoton]

        if 'gif' in ActualBoton:
            return
        if 'Titulo' in ActualBoton:
            TituloBoton = "{}".format(ActualBoton['Titulo'])
        else:
            TituloBoton = ''

        if 'OBS' in ActualBoton:
            ActualizarEstadoOBS(ActualBoton)

        if 'ico' in ActualBoton:
            NombreIcono = "{}".format(ActualBoton['ico'])
        elif 'Regresar' in ActualBoton and 'ico_Regresar' in Data:
            NombreIcono = Data['ico_Regresar']
        elif 'Siquiente' in ActualBoton and 'ico_Siquiente' in Data:
            NombreIcono = Data['ico_Siquiente']
        elif 'Anterior' in ActualBoton and 'ico_Anterior' in Data:
            NombreIcono = Data['ico_Anterior']
        elif 'Estado' in ActualBoton:
            if ActualBoton['Estado'] and 'icon_true' in ActualBoton:
                NombreIcono = ActualBoton['icon_true']
            elif not ActualBoton['Estado'] and 'icon_false' in ActualBoton:
                NombreIcono = ActualBoton['icon_false']
            elif 'ico_defecto' in Data:
                NombreIcono = Data['ico_defecto']
            else:
                NombreIcono = "imagen.png"
        elif 'ico_defecto' in Data:
            NombreIcono = Data['ico_defecto']
        else:
            NombreIcono = "imagen.png"

        if 'Titulo_Color' in ActualBoton:
            ColorTexto = ActualBoton['Titulo_Color']
        else:
            ColorTexto = "white"

        DirecionIcono = os.path.join(os.path.dirname(__file__), '..') + "/" + NombreIcono
        if os.path.exists(DirecionIcono):
            Icono = Image.open(DirecionIcono).convert("RGBA")
            if TituloBoton:
                Icono.thumbnail((ImagenBoton.width, ImagenBoton.height - 20), Image.LANCZOS)
            else:
                Icono.thumbnail((ImagenBoton.width, ImagenBoton.height), Image.LANCZOS)
        else:
            Imprimir(f"No se encontro imagen {DirecionIcono}")
            Icono = Image.new(mode="RGBA", size=(256, 256), color=(153, 153, 255))
            Icono.thumbnail((ImagenBoton.width, ImagenBoton.height), Image.LANCZOS)

        IconoPosicion = ((ImagenBoton.width - Icono.width) // 2, 0)
        ImagenBoton.paste(Icono, IconoPosicion, Icono)

        if TituloBoton:
            dibujo = ImageDraw.Draw(ImagenBoton)
            font = ImageFont.truetype(FuenteBoton, 14)
            label_w, label_h = dibujo.textsize(TituloBoton, font=font)
            label_pos = ((ImagenBoton.width - label_w) // 2, ImagenBoton.height - 20)
            dibujo.text(label_pos, text=TituloBoton, font=font, fill=ColorTexto)

        Deck.set_key_image(IndiceBoton + DesfaceBoton, PILHelper.to_native_format(Deck, ImagenBoton))
    else:
        Deck.set_key_image(IndiceBoton, PILHelper.to_native_format(Deck, ImagenBoton))


def ActualizarGif(MiDeck, IndiceBoton):
    Deck = MiDeck.Deck
    BotonActuales = MiDeck.BotonActuales
    DesfaceBoton = MiDeck.DesfaceBoton
    if(IndiceBoton + DesfaceBoton < 0 or IndiceBoton + DesfaceBoton > Deck.key_count()):
        return
    ActualBoton = BotonActuales[IndiceBoton]
    if 'gif' in ActualBoton:
        if 'gif_cargado' in ActualBoton:
            Deck.set_key_image(IndiceBoton, next(ActualBoton['gif_cargado']))
        else:
            ActualBoton['gif_cargado'] = CrearGif(MiDeck.Deck, ActualBoton['gif'])
        return


def DefinirFuente(_Fuente):
    global FuenteBoton
    FuenteBoton = os.path.join(os.path.dirname(__file__), '..') + "/" + _Fuente


def CrearGif(deck, Archivo_Gif):
    icon_frames = list()
    Archivo_Gif = os.path.join(os.path.dirname(__file__), '..') + "/" + Archivo_Gif
    icon = Image.open(Archivo_Gif)
    for frame in ImageSequence.Iterator(icon):
        frame_image = PILHelper.create_scaled_image(deck, frame)
        native_frame_image = PILHelper.to_native_format(deck, frame_image)
        icon_frames.append(native_frame_image)
    return itertools.cycle(icon_frames)


def ActualizarEstadoOBS(ActualBoton):
    if ActualBoton['OBS'] == "Esena" and "Esena" in ActualBoton:
        EsenaActual = ObtenerDato("/Data/OBS.json", "EsenaActual")
        if ActualBoton['Esena'] == EsenaActual:
            ActualBoton['Estado'] = True
        else:
            ActualBoton['Estado'] = False
    elif ActualBoton['OBS'] == "Grabar":
        EstadoGrabacion = ObtenerDato("/Data/OBS.json", "EstadoGrabando")
        if EstadoGrabacion:
            ActualBoton['Estado'] = True
        else:
            ActualBoton['Estado'] = False
    elif ActualBoton['OBS'] == "Live":
        EstadoGrabacion = ObtenerDato("/Data/OBS.json", "EstadoLive")
        if EstadoGrabacion:
            ActualBoton['Estado'] = True
        else:
            ActualBoton['Estado'] = False


def IniciarAnimacion(MiDeck):
    Data = MiDeck.Data
    if 'Gif_fps' in Data:
        Gif_fps = Data['Gif_fps']
    else:
        Gif_fps = 10
    threading.Thread(target=Animacion, args=[MiDeck, Gif_fps]).start()


def Animacion(MiDeck, fps):
    tiempo_frame = Fraction(1, fps)
    siquiente_frame = Fraction(time.monotonic())
    while True:
        try:
            Deck = MiDeck.Deck
            BotonActuales = MiDeck.BotonActuales
            with Deck:
                for IndiceBoton in range(len(BotonActuales)):
                    ActualizarGif(MiDeck, IndiceBoton)
        except TransportError as err:
            print("TransportError: {0}".format(err))
            break

        siquiente_frame += tiempo_frame
        tiempo_espera = float(siquiente_frame) - time.monotonic()
        if tiempo_espera >= 0:
            time.sleep(tiempo_espera)
