#!/usr/bin/env python3
# TODO: agregar git https://python-elgato-streamdeck.readthedocs.io/en/stable/examples/animated.html
# TODO: Agregar siquiente automaticamente
# TODO: Reordenar codigo
# TODO: Emular Raton
# BUG: Error cargando sin folder
# Librerias
import os
import threading
import time

# Librerias de ElGato
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
# Librerias para idenficiar Teclado
from evdev import InputDevice, categorize, ecodes
import argparse

import Extra.FuncionesOBS as OBSWebSocketPropios
import Extra.MiMQTT as MiMQTTs
import Extra.MiDeck as MiDecks

# Cargar funciones de Archivos
from Extra.FuncionesProyecto import SalvarProyecto, CargarProyecto, AbirProyecto, CargarIdVideo
from Extra.News import SalvarArchivoNoticia
from Extra.EmularTeclado import ComandoTeclas, ComandoEscribir
from Extra.Depuracion import Imprimir, CambiarDepuracion
from Extra.YoutubeChat import SalvarChatYoutube
from Extra.CargarData import CargarData
from Extra.Hilos import CargarHilo

# TODO: ordenar para no usar variable globales
MiDeck = "nada"
teclas = "nada"
ComandosRaton = "nada"
folder = ""
fuente = ""
data = ""
DefaceBotones = 0

MiOBS = OBSWebSocketPropios.MiObsWS()
MiMQTT = MiMQTTs.MiMQTT()
# TODO: Agregar sonidos
parser = argparse.ArgumentParser(description='Heramienta de creacion de contenido de ALSW')
parser.add_argument('--master', '-m', help="Cargar servidor de %(prog)s",  action="store_true")
parser.add_argument('--cliente', '-c', help="Cargando cliente de %(prog)s",  action="store_true")
parser.add_argument('--deck', '-d', help="Solo usar StreamDeck",  action="store_true")
parser.add_argument('--ratom', '-r', help="Solo usar Ratom Razer",  action="store_true")
parser.add_argument('--nodepurar', '-nd', help="Acivar modo sin depuracion", action="store_true")
parser.add_argument('--proyecto', '-p', help="Configurar folder a proyecto actual", action="store_true")
parser.add_argument('--noticias', '-n', help="Configurar folder a noticias actual")
parser.add_argument('--salvaryoutube', '-sy', help="Salva el chat en un archivo", action="store_true")
parser.add_argument('--deckdemo', '-dd', help="Solo usar StreamDeck",  action="store_true")

#  Codigo del Raton_Razer


def CargandoRaton():
    '''Cargas las configuraciones del Teclado Ratom'''
    global data
    global ComandosRaton
    Imprimir("Cargando Raton Razer")
    ComandosRaton = data['teclado']
    if 'Raton_Razer' in data:
        Raton = InputDevice(data['Raton_Razer'])
        Raton.grab()
        HiloRazer = threading.Thread(target=HiloRaton, args=(Raton,), daemon=True)
        HiloRazer.start()
    else:
        Imprimir("error Raron Razer no definido")


def HiloRaton(Raton):
    '''Hila del teclado del Raton'''
    global ComandosRaton
    for event in Raton.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            if key.keystate == key.key_down:
                for teclas in ComandosRaton:
                    if 'Boton' in teclas:
                        if teclas['Boton'] == key.keycode:
                            Imprimir(f"Raton {key.keycode} - {teclas['Nombre']}")
                            ActualizarAccion(teclas)


# Principal
if __name__ == "__main__":
    args = parser.parse_args()
    if args.nodepurar:
        CambiarDepuracion(False)

    if args.master:
        Imprimir("Modo Master")
        data = CargarData('Comandos.json')
        CargandoRaton()
        # CargandoElGato()
        CargarHilo()
    elif args.cliente:
        Imprimir("Modo Cliente MQTT")
    elif args.deck:
        Imprimir("Modo Solo StreamDeck")
        data = CargarData('Comandos.json')
        # CargandoElGato()
        CargarHilo()
    elif args.ratom:
        Imprimir("Modo Solo Raton Razer")
        data = CargarData('Comandos.json')
        CargandoRaton()
        CargarHilo()
    elif args.proyecto:
        Imprimir("Configurando Folder como Proyecto Actual")
        SalvarProyecto(os.getcwd())
    elif args.noticias:
        Imprimir("Configurar Folder para Noticias Actual")
        SalvarArchivoNoticia(os.getcwd() + "/" + args.noticias)
    elif args.salvaryoutube:
        Imprimir("Emezandoa a guardar Chat en Proyecto Actual")
        SalvarChatYoutube(CargarProyecto(), CargarIdVideo())
    elif args.deckdemo:
        Imprimir("Demo de StreamDeck con nuevas Librerias")
        data = CargarData('Comandos.json')
        Deck = MiDecks.MiDeck(data)
        CargarHilo()
    else:
        Imprimir("No parametro")
        data = CargarData('Comandos.json')
        CargandoRaton()
        # CargandoElGato()
        CargarHilo()
