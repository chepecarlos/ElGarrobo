#!/usr/bin/env python3

# Librerias
import os
import threading
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
import pyautogui
import json
import websocket

teclas = "nada"
folder = ""
fuente = ""

# Recusos para sistema
FolderRecursos = os.path.join(os.path.dirname(__file__), "Recusos")

with open('Comandos.json') as f:
    data = json.load(f)

def ComandoTeclas(Teclas):

    for tecla in Teclas:
        pyautogui.keyDown(tecla)

    for tecla in reversed(Teclas):
        pyautogui.keyUp(tecla)

def ActualizarImagen(deck, teclas, tecla, limpiar = False):
    global folder

    image = PILHelper.create_image(deck)

    if not limpiar:
        nombre = "{}".format(teclas[tecla]['Nombre'])

        if 'Regresar' in teclas[tecla]:
            if 'ico' in teclas[tecla]:
                NombreIcon = "{}".format(teclas[tecla]['ico'])
            elif 'ico_Regresar' in data :
                NombreIcon = data['ico_Regresar']
            else:
                NombreIcon = "imagen.png"
        elif 'Estado' in teclas[tecla]:
            if teclas[tecla]['EstadoActual'] and 'ico' in teclas[tecla]['Estado'][0]:
                NombreIcon = teclas[tecla]['Estado'][0]['ico']
            elif not teclas[tecla]['EstadoActual'] and 'ico' in teclas[tecla]['Estado'][1]:
                NombreIcon = teclas[tecla]['Estado'][1]['ico']
            elif 'ico_defecto' in data:
                NombreIcon = data['ico_defecto']
            else:
                NombreIcon = "imagen.png"
        elif 'ico' in teclas[tecla]:
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

        titulo = ''

        if 'Estado' in teclas[tecla]:
            if teclas[tecla]['EstadoActual'] and 'Titulo' in teclas[tecla]['Estado'][0]:
                titulo = "{}".format(teclas[tecla]['Estado'][0]['Titulo'])
            elif not teclas[tecla]['EstadoActual'] and 'Titulo' in teclas[tecla]['Estado'][1]:
                titulo = "{}".format(teclas[tecla]['Estado'][1]['Titulo'])
        elif 'Titulo' in teclas[tecla]:
            titulo = "{}".format(teclas[tecla]['Titulo'])


        if not titulo == '':
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
                teclas = data['Comando']
                for key in range(deck.key_count()):
                    ActualizarImagen(deck, teclas, key, True)
                for tecla in range(len(teclas)):
                    ActualizarImagen(deck, teclas, tecla)
            elif 'OS' in teclas[tecla]:
                os.system(teclas[tecla]['OS'])
            elif 'websocket' in teclas[tecla]:
                ComandoWebSocket(teclas[tecla]['websocket'])
            elif 'EstadoActual' in teclas[tecla]:
                teclas[tecla]['EstadoActual'] = not teclas[tecla]['EstadoActual']
                ActualizarImagen(deck, teclas, tecla)
                teclasGuardar = teclas
                teclas = teclas[tecla]['Estado']
                if teclasGuardar[tecla]['EstadoActual']:
                    ActualizarTeclas(deck,  0, True)
                else:
                    ActualizarTeclas(deck,  1, True)
                teclas = teclasGuardar
            elif 'tecla' in teclas[tecla]:
                ComandoTeclas(teclas[tecla]['tecla'])
            elif 'Key' in teclas[tecla]:
                teclas = teclas[tecla]['Key']
                for key in range(deck.key_count()):
                    ActualizarImagen(deck, teclas, key, True)
                for indice in range(len(teclas)):
                    ActualizarImagen(deck, teclas, indice)
            else:
                print("Tecla no definida")
        else:
            print("Tecla no programada")

def ComandoWebSocket(comando):
    if 'Servidor' in data:
        ws = websocket.WebSocket()
        Servidor = "ws://{}:8765".format(data['Servidor'])
        print(Servidor)
        ws.connect(Servidor)
        ws.send(comando)
        # print ("Reciviendo...")
        # result = ws.recv()
        print ("comando enviado")
        ws.close()

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
        deck.set_key_callback(ActualizarTeclas)

        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
