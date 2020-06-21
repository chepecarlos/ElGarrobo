#!/usr/bin/env python3

# Librerias
import os
import sys
import threading
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
import json

from EmularTeclado import *
from OBSWebSocketPropio import *
# from MiWebSoket import *
from MiMQTT import *

# TODO: ordenar para no usar variable globales
MiDeck = "nada"
teclas = "nada"
folder = ""
fuente = ""

DefaceBotones = 0

MiOBS = MiObsWS()
MiMQTT = MiMQTT()

# Recusos para sistema
FolderRecursos = os.path.join(os.path.dirname(__file__), "Recusos")

# print(os.listdir())

if os.path.exists('Comandos.json'):
    # Todo: Cambiaf carga de un solo archivo
    with open('Comandos.json') as f:
        data = json.load(f)
else:
    print("No se Encontro el Archivo Comandos.json")
    sys.exit()


def ActualizarImagen(deck, teclas, tecla, limpiar = False):
    global folder
    global DefaceBotones

    image = PILHelper.create_image(deck)
    if not limpiar:
        nombre = "{}".format(teclas[tecla]['Nombre'])
        if 'Regresar' in teclas[tecla]:
            if 'ico' in teclas[tecla]:
                NombreIcon = "{}".format(teclas[tecla]['ico'])
            elif 'ico_Regresar' in data:
                NombreIcon = data['ico_Regresar']
            else:
                NombreIcon = "imagen.png"
        elif 'Estado' in teclas[tecla]:
            # print("Hay estado {}".format(teclas[tecla]['Estado']))
            if teclas[tecla]['Estado'] and 'icon_true' in teclas[tecla]:
                NombreIcon = teclas[tecla]['icon_true']
            elif not teclas[tecla]['Estado'] and 'icon_false' in teclas[tecla]:
                NombreIcon = teclas[tecla]['icon_false']
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

        if 'Titulo' in teclas[tecla]:
            titulo = "{}".format(teclas[tecla]['Titulo'])

        if not titulo == '':
            dibujo = ImageDraw.Draw(image)
            font = ImageFont.truetype(fuente, 14)
            label_w, label_h = dibujo.textsize(titulo, font=font)
            label_pos = ((image.width - label_w) // 2, image.height - 20)
            dibujo.text(label_pos, text=titulo, font=font, fill="white")
    # TODO: Mejor logica de deface
    if(tecla + DefaceBotones < 0 or tecla + DefaceBotones > deck.key_count()):
        return
    deck.set_key_image(tecla + DefaceBotones, PILHelper.to_native_format(deck, image))


def ActualizarTeclas(deck, tecla, estado):

    global teclas
    global DefaceBotones
    tecla = tecla - DefaceBotones
    if estado:
        if tecla < len(teclas):
            print(f"Boton {tecla} - {teclas[tecla]['Nombre']}")

            if 'Regresar' in teclas[tecla]:
                teclas = data['Comando']
                DefaceBotones = 0
                BorrarActualizarImagenes()
            elif 'Siquiente' in teclas[tecla]:
                print("Se preciono next")
                DefaceBotones -= deck.key_count()
                BorrarActualizarImagenes()
            elif 'Anterior' in teclas[tecla]:
                print("Se preciono next")
                DefaceBotones += deck.key_count()
                BorrarActualizarImagenes()
            elif 'Filtro' in teclas[tecla] and 'Fuente' in teclas[tecla]:
                MiOBS.CambiarFiltro(teclas[tecla]['Fuente'], teclas[tecla]['Filtro'], teclas[tecla]['Estado'])
            elif 'Fuente' in teclas[tecla]:
                MiOBS.CambiarFuente(teclas[tecla]['Fuente'], not teclas[tecla]['Estado'])
            elif 'CambiarEsena' in teclas[tecla]:
                MiOBS.CambiarEsena(teclas[tecla]['CambiarEsena'])
            elif 'Grabar' in teclas[tecla]:
                MiOBS.CambiarGrabacion()
            elif 'Live' in teclas[tecla]:
                MiOBS.CambiarStriming()
            elif 'OS' in teclas[tecla]:
                os.system(teclas[tecla]['OS'])
            elif 'mqtt' in teclas[tecla]:
                print(f"Comando MQTT {teclas[tecla]['mqtt']}")
                MiMQTT.Enviando(teclas[tecla]['mqtt'])
            elif 'tecla' in teclas[tecla]:
                ComandoTeclas(teclas[tecla]['tecla'])
            elif 'Opcion' in teclas[tecla]:
                if teclas[tecla]['Opcion'] == "OBS_Local" and 'OBS_Local' in data:
                    print("Conectando con Sevidor local OBS")
                    MiOBS.CambiarHost(data['OBS_Local'])
                    MiOBS.Conectar()
                    MiOBS.RegistarEvento(EventoOBS)
                elif teclas[tecla]['Opcion'] == "OBS_Remoto" and 'OBS_Remoto' in data:
                    print("Conectando con Sevidor Remoto OBS")
                    MiOBS.CambiarHost(data['OBS_Remoto'])
                    MiOBS.Conectar()
                    MiOBS.RegistarEvento(EventoOBS)
                # TODO; hacer configuraciones base de obs
                elif teclas[tecla]['Opcion'] == "MQTT_Remoto" and 'MQTT_Remoto' in data:
                    print(f"Intentando MQTT_Remoto {data['MQTT_Remoto']}")
                    MiMQTT.CambiarHost(data['MQTT_Remoto'])
                    MiMQTT.Conectar()
                elif teclas[tecla]['Opcion'] == "Exit":
                    # TODO: ver si esta habierto antes de cerrar
                    MiOBS.Cerrar()
                    MiMQTT.Cerrar()
                    deck.reset()
                    deck.close()
                    print("Saliendo ElGato ALSW - Adios :) ")
                else:
                    print(f"Opcion: {teclas[tecla]['Opcion']}")
                    # TODO: Desconectar OBS y WebSocket
            elif 'Key' in teclas[tecla]:
                teclas = teclas[tecla]['Key']
                BorrarActualizarImagenes()
            else:
                print("Tecla no definida")
        else:
            print("Tecla no programada")


def ActualizarImagenes():
    for indice in range(len(teclas)):
        ActualizarImagen(deck, teclas, indice)


def BorrarActualizarImagenes():
    # TODO: Mejorar la logica de guardad en tiemporal
    global DefaceBotones
    Tmp = DefaceBotones
    DefaceBotones = 0
    for key in range(deck.key_count()):
        ActualizarImagen(deck, teclas, key, True)
    DefaceBotones = Tmp
    ActualizarImagenes()


def EventoOBS(mensaje):
    IdOBS = BuscarCarpeta('OBS')
    if IdOBS == -1:
        print("Error no encontado Botones")
        return
    if(mensaje.name == 'RecordingStopped'):
        print('Parado la grabacion')
        IdGrabar = BuscarBoton(IdOBS, 'Rec')
        data['Comando'][IdOBS]['Key'][IdGrabar]['Estado'] = False
        ActualizarImagenes()
    elif(mensaje.name == 'RecordingStarted'):
        print('Iniciado la grabacion')
        IdGrabar = BuscarBoton(IdOBS, 'Rec')
        data['Comando'][IdOBS]['Key'][IdGrabar]['Estado'] = True
        ActualizarImagenes()
    elif(mensaje.name == 'StreamStopped'):
        print("Parando la trasmicion")
        IdLive = BuscarBoton(IdOBS, 'Live')
        data['Comando'][IdOBS]['Key'][IdLive]['Estado'] = False
        ActualizarImagenes()
    elif(mensaje.name == 'StreamStarted'):
        print("Empezando la trasmicion")
        IdLive = BuscarBoton(IdOBS, 'Live')
        data['Comando'][IdOBS]['Key'][IdLive]['Estado'] = True
        ActualizarImagenes()
    elif(mensaje.name == 'SwitchScenes'):
        print(f"Cambia a Esena {mensaje.datain['scene-name']}")
        EsenaActiva = BuscarBoton(IdOBS, mensaje.datain['scene-name'])
        for tecla in range(len(data['Comando'][IdOBS]['Key'])):
            if EsEsena(IdOBS, tecla):
                if(EsenaActiva == tecla):
                    data['Comando'][IdOBS]['Key'][tecla]['Estado'] = True
                else:
                    data['Comando'][IdOBS]['Key'][tecla]['Estado'] = False
        ActualizarImagenes()
    elif(mensaje.name == 'SceneItemVisibilityChanged'):
        NombreIten = mensaje.datain['item-name']
        EstadoItem = mensaje.datain['item-visible']
        IdItem = BuscarBoton(IdOBS, NombreIten)
        print(f"Se cambio fuente {NombreIten} - {EstadoItem}")
        data['Comando'][IdOBS]['Key'][IdItem]['Estado'] = EstadoItem
        ActualizarImagenes()
    elif(mensaje.name == 'SourceFilterVisibilityChanged'):
        NombreFiltro = mensaje.datain['filterName']
        NombreFuente = mensaje.datain['sourceName']
        EstadoFiltro = mensaje.datain['filterEnabled']
        print(f"Se cambio el filtro {NombreFiltro} de {NombreFuente} a {EstadoFiltro}")
        IdItem = BuscarBoton(IdOBS, NombreFiltro)
        data['Comando'][IdOBS]['Key'][IdItem]['Estado'] = EstadoFiltro
        ActualizarImagenes()
    else:
        print(f"Evento no procesado de OBS: {mensaje}")


def BuscarCarpeta(nombre):
    for tecla in range(len(data['Comando'])):
        if(data['Comando'][tecla]['Nombre'] == nombre):
            return tecla
    return -1


def BuscarBoton(IdFolder, nombre):
    if(IdFolder == -1):
        return -1
    for tecla in range(len(data['Comando'][IdFolder]['Key'])):
        if(data['Comando'][IdFolder]['Key'][tecla]['Nombre'] == nombre):
            return tecla
    return -1


def EsEsena(IdFolder, IdEsena):
    if('CambiarEsena' in data['Comando'][IdFolder]['Key'][IdEsena]):
        return True
    return False


def BuscandoBoton(NombreFolder, NombreBoton):
    IdFolder = BuscarCarpeta(NombreFolder)
    return BuscarBoton(IdFolder, NombreBoton)


# Principal
if __name__ == "__main__":

    # Buscando Dispisitovos
    streamdecks = DeviceManager().enumerate()

    print(f"Programa El Gato ALSW - {'Encontrado' if len(streamdecks) > 0 else 'No Conectado'}")

    for index, deck in enumerate(streamdecks):

        MiDeck = deck
        # Abriendo puerto
        deck.open()
        deck.reset()

        print(f"Abriendo '{deck.deck_type()}' dispositivo (Numero Serial: '{deck.get_serial_number()}')")

        # Cambiar Brillo
        if 'Brillo' in data:
            deck.set_brightness(data['Brillo'])
        else:
            deck.set_brightness(50)

        if 'Fuente' in data:
            fuente = f"{data['Fuente']}"
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
