import os

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from Extra.Depuracion import Imprimir


def ActualizarIcono(Deck, BotonActuales, IndiceBoton, Data, Limpiar=False):
    global DesfaceBoton
    global FuenteBoton

    if(IndiceBoton + DesfaceBoton < 0 or IndiceBoton + DesfaceBoton > Deck.key_count()):
        return

    ImagenBoton = PILHelper.create_image(Deck)
    ActualBoton = BotonActuales[IndiceBoton]

    if not Limpiar:
        if 'Titulo' in ActualBoton:
            TituloBoton = "{}".format(ActualBoton['Titulo'])
        else:
            TituloBoton = ''

        if 'ico' in ActualBoton:
            NombreIcono = "{}".format(ActualBoton['ico'])
        elif 'Regresar' in ActualBoton and 'ico_Regresar' in Data:
            NombreIcono = Data['ico_Regresar']
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
        print(DirecionIcono)
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


def DefinirFuente(_Fuente):
    global FuenteBoton
    FuenteBoton = os.path.join(os.path.dirname(__file__), '..') + "/" + _Fuente


def DefinirDesface(_Desface=0):
    global DesfaceBoton
    DesfaceBoton = _Desface
