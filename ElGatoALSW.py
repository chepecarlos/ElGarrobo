#!/usr/bin/env python3

# Librerias
import os
import threading
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from pynput.keyboard import Key, Controller


keyboard = Controller()

# Recusos para sistema
FolderRecursos = os.path.join(os.path.dirname(__file__), "Recursos")

Estado = 0

Comandos = [["Arduino", [["Verificar", [Key.ctrl, "r"]], ["Salvar", [Key.ctrl, "s"]]]]]



def PrecionarTecla(deck, key, state):
    print("Boton {} = {}".format(Comandos[key][0], state), flush=True)

    CambiarImagen(deck, key, state)

def ObtenerImagen(deck, key, state):
    name = "{}".format(Comandos[key][0])
    icon = "{}{}.png".format(Comandos[key][0],"P" if state else "R")
    font = "Roboto-Regular.ttf"
    label = "{}".format(Comandos[key][0])

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

    # Load a custom TrueType font and Comandosuse it to overlay the key index, draw key
    # label onto the image.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    label_w, label_h = draw.textsize(label_text, font=font)
    label_pos = ((image.width - label_w) // 2, image.height - 20)
    draw.text(label_pos, text=label_text, font=font, fill="white")
    return PILHelper.to_native_format(deck, image)


# Actualizar
def CambiarImagen(deck, key, state):

    # Obtener Imagen
    ImagenEstilo = ObtenerImagen(deck, key, state)

    #
    Imagen = CargarImagen(deck, ImagenEstilo["icon"], ImagenEstilo["font"], ImagenEstilo["label"])

    deck.set_key_image(key, Imagen)

def ComandoTeclas(Teclas):
    for tecla in Teclas:
        keyboard.press(tecla)

    for tecla in Teclas:
        keyboard.release(tecla)
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
        for key in range(len(Comandos)):
            CambiarImagen(deck, key, False)

        deck.set_key_callback(PrecionarTecla)
        # Sistema de Coalbask
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
