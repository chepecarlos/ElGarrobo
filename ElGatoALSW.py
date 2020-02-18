#!/usr/bin/env python3

# Librerias
import os
import threading
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# Recusos para sistema
FolderRecursos = os.path.join(os.path.dirname(__file__), "Recursos")

# Variables Globass
Carpeta = ["Arduino","Blender"]

def ActualizarImagen(deck, key, state):
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

def ObtenerImagen(deck, key, state):
    name = "{}".format(Carpeta[key])
    icon = "{}{}.png".format(Carpeta[key],"P" if state else "R")
    font = "Roboto-Regular.ttf"
    label = "{}".format(Carpeta[key])

    return {
        "name": name,
        "icon": os.path.join(FolderRecursos, icon),
        "font": os.path.join(FolderRecursos, font),
        "label": label
    }

#
def CargarImagen(deck, icon_filename, font_filename, label_text):
    # Create new key image of the correct dimensions, black background.
    image = PILHelper.create_image(deck)

    # Resize the source image asset to best-fit the dimensions of a single key,
    # and paste it onto our blank frame centered as closely as possible.
    icon = Image.open(icon_filename).convert("RGBA")
    icon.thumbnail((image.width, image.height - 20), Image.LANCZOS)
    icon_pos = ((image.width - icon.width) // 2, 0)
    image.paste(icon, icon_pos, icon)

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    label_w, label_h = draw.textsize(label_text, font=font)
    label_pos = ((image.width - label_w) // 2, image.height - 20)
    draw.text(label_pos, text=label_text, font=font, fill="white")

    return PILHelper.to_native_format(deck, image)


# Actualizar
def CambiarImagen(deck, key, state):
    print("Cargando {}".format(Carpeta[key]))

    # Obtener Imagen
    ImagenEstilo = ObtenerImagen(deck, key, state)

    #
    Imagen = CargarImagen(deck, ImagenEstilo["icon"], ImagenEstilo["font"], ImagenEstilo["label"])

    deck.set_key_image(key, Imagen)

# Principal
if __name__ == "__main__":

    # Buscando Dispisitovos
    streamdecks = DeviceManager().enumerate()

    print("Programa El Gato ALSW - {}".format("Encontrado" if len(streamdecks) > 0 else "No Conectado"));

    for index, deck in enumerate(streamdecks):

        # Abriendo puerto
        deck.open()
        deck.reset()

        print("Abriendo '{}' dispositivo (Numero Serial: '{}')".format(deck.deck_type(), deck.get_serial_number()))

        # Cambiar Brillo
        deck.set_brightness(50)

        # Activando Imagen Defecto
        for key in range(len(Carpeta)):
            CambiarImagen(deck, key, False)

        deck.set_key_callback()

        # Sistema de Coalbask
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
