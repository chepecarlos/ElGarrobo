#!/usr/bin/python3
# -*- coding: utf-8 -*-

# TODO: agregar git https://python-elgato-streamdeck.readthedocs.io/en/stable/examples/animated.html
# Librerias
import os
import argparse

import Extra.MiDeck as MiDecks

# Cargar funciones de Archivos
from Extra.FuncionesProyecto import SalvarProyecto, CargarProyecto, CargarIdVideo
from Extra.News import SalvarArchivoNoticia
from Extra.Depuracion import Imprimir, CambiarDepuracion
from Extra.YoutubeChat import SalvarChatYoutube
from Extra.CargarData import CargarData
from Extra.Hilos import CargarHilo


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


# Principal
if __name__ == "__main__":
    args = parser.parse_args()
    if args.nodepurar:
        CambiarDepuracion(False)

    if args.master:
        Imprimir("Modo Master")
        data = CargarData('Comandos.json')
        # CargandoRaton()
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
        # CargandoRaton()
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
        Deck = MiDecks.MiDeck(data)
        CargarHilo()
