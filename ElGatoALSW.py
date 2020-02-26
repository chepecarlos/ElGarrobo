#!/usr/bin/env python3

# Librerias
import os
import threading
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from pynput.keyboard import Key, Controller
import time
import json

# Cargar Teclado
keyboard = Controller()

teclas = "nada"
folder = ""
fuente = "."

# Recusos para sistema
FolderRecursos = os.path.join(os.path.dirname(__file__), "Recusos")

Estado = -1

with open('Comandos.json') as f:
    data = json.load(f)

def PrecionarTecla(deck, key, state):
    global Estado
    if Estado == -1:
        if key < len(Comandos):
            print("Boton {} = {}".format(Comandos[key][0], state), flush=True)
            CambiarImagen(deck, key, state)
            Estado = key
            for key in range(len(Comandos[key][1])):
                CambiarImagen(deck, key, False)
            CambiarImagen(deck, deck.key_count() - 1  , False, False)
        else:
            print("Teclado no programada")
    else:
        if key == deck.key_count() -1:
            deck.reset()
            Estado = -1;
            for key in range(len(Comandos)):
                CambiarImagen(deck, key, False)
            print("Regresar")
        elif key < len(Comandos[Estado][1]):
            print("Boton {} = {}".format(Comandos[Estado][1][key][0], state), flush=True)
            CambiarImagen(deck, key, state)
            if state:
                ComandoTeclas(Comandos[Estado][1][key][1])
        else:
            print("Teclado no programada")
    if state:
        time.sleep(0.25)



def ComandoTeclas(Teclas):
    for tecla in Teclas:
        if tecla == 'ctrl':
            keyboard.press(Key.ctrl)
        elif tecla == 'alt':
            keyboard.press(Key.alt)
        else:
            keyboard.press(tecla)

    for tecla in Teclas:
        if tecla == 'ctrl':
            keyboard.press(Key.ctrl)
        elif tecla == 'alt':
            keyboard.press(Key.alt)
        else:
            keyboard.press(tecla)

def ActualizarImagen(deck, teclas, tecla, limpiar = False):
    global folder

    image = PILHelper.create_image(deck)

    if not limpiar:
        nombre = "{}".format(teclas[tecla]['Nombre'])

        if 'ico' in teclas[tecla]:
            NombreIcon = "{}".format(teclas[tecla]['ico'])
        else:
            if 'ico_defecto' in data:
                NombreIcon = data['ico_defecto']
            else:
                NombreIcon = "imagen.png"

        icon = Image.open(NombreIcon).convert("RGBA")
        icon.thumbnail((image.width, image.height - 20), Image.LANCZOS)
        icon_posicion = ((image.width - icon.width) // 2, 0)
        image.paste(icon, icon_posicion, icon)

        if 'Titulo' in teclas[tecla]:
            titulo = "{}".format(teclas[tecla]['Titulo'])
            dibujo = ImageDraw.Draw(image)
            font = ImageFont.truetype(fuente, 14)
            label_w, label_h = dibujo.textsize(titulo, font=font)
            label_pos = ((image.width - label_w) // 2, image.height - 20)
            dibujo.text(label_pos, text=titulo, font=font, fill="white")

    deck.set_key_image(tecla, PILHelper.to_native_format(deck, image))

def ActualizarTeclas(deck, tecla, estado):
    global teclas

    if estado:
        if tecla < len(teclas):
            print("Boton {} - {}".format(tecla, teclas[tecla]['Nombre']), flush=True)

            if 'Regresar' in teclas[tecla]:
                print("Regresar")
                teclas = data['Comando']
                for key in range(deck.key_count()):
                    ActualizarImagen(deck, teclas, key, True)
                for tecla in range(len(teclas)):
                    ActualizarImagen(deck, teclas, tecla)
            elif 'tecla' in teclas[tecla]:
                print("comando {}".format(teclas[tecla]['tecla']))
                ComandoTeclas(teclas[tecla]['tecla'])
            else:
                print("Entando a folder")
                teclas = teclas[tecla]['Key']
                for key in range(deck.key_count()):
                    ActualizarImagen(deck, teclas, key, True)
                for indice in range(len(teclas)):
                    ActualizarImagen(deck, teclas, indice)
        else:
            print("Tecla no programada")

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
        if 'Brillo' in data:
            deck.set_brightness(data['Brillo'])
        else:
            deck.set_brightness(50)

        if 'Fuente' in data:
            fuente = "{}".format(data['Fuente'])
        else:
            print("Fuente no asignada")
            deck.close()


        teclas = data['Comando']
        for tecla in range(len(teclas)):
            ActualizarImagen(deck, teclas, tecla)

        # Sistema de Coalbask
        # deck.set_key_callback(PrecionarTecla)
        deck.set_key_callback(ActualizarTeclas)

        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
