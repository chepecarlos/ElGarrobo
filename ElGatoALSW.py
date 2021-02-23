#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Librerias
import os
import argparse
import sys
import Extra.MiDeck as MiDecks
import Extra.ElGatito as ElGatitos

# Cargar funciones de Archivos
from Extra.FuncionesProyecto import SalvarProyecto, CargarProyecto, CargarIdVideo, CrearFolderProyecto
from Extra.News import SalvarArchivoNoticia
from Extra.Depuracion import Imprimir, CambiarDepuracion
from Extra.YoutubeChat import SalvarChatYoutube
from Extra.CargarData import CargarData
from Extra.Hilos import CargarHilo
from Extra.FuncionesBlender import CrearProxy, RenderizarVideo, BorrarTemporalesBender
from Extra.ApiYoutube import ActualizarDescripcion, ActualizarDescripcionFolder


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
parser.add_argument('--blenderproxy', '-bp', help="Creando proxy de Blender",  action="store_true")
parser.add_argument('--blenderrenderizar', '-br', help="Empezando a Renderizar Video")
parser.add_argument('--blenderborrar', '-bb', help="Borrar Temporales", action="store_true")
parser.add_argument('--folderproyecto', '-fp', help="Creando folder proyecto de video")
parser.add_argument('--video-id', '-vi', help="ID del video a actualizar descripcipn en Youtube")
parser.add_argument("--descripcion", '-vd', help="ID del video a actualizar descripcipn en Youtube")
parser.add_argument("--youtube-descripcion", '-yd', help="Actualiza todos las descripciones de los video del folder", action="store_true")


if sys.version_info[0] < 3:
    Imprimir('Tienes que usar Python 3 para este programa')
    sys.exit(1)

# Principal
if __name__ == "__main__":
    args = parser.parse_args()

    if args.nodepurar:
        CambiarDepuracion(False)

    if args.master:
        Imprimir("Modo Master")
        data = CargarData('Comandos.json')
        ElGatitos.ElGatito(data)
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
    elif args.blenderproxy:
        Imprimir("Empezando a crear proxy")
        CrearProxy(os.getcwd())
    elif args.blenderrenderizar:
        Imprimir("Empezando a Renderizar video")
        RenderizarVideo(args.blenderrenderizar)
    elif args.blenderborrar:
        Imprimir("Borrar temporales de Blender")
        BorrarTemporalesBender('BL_proxy')
        BorrarTemporalesBender('bpsrender')
    elif args.folderproyecto:
        Imprimir(f"Creando folder de Proyecto {args.folderproyecto}")
        CrearFolderProyecto(args.folderproyecto)
    elif args.video_id:
        Imprimir(f"Actualizando descripcion del Video {args.video_id}")
        if args.descripcion:
            ActualizarDescripcion(args.video_id, args.descripcion)
        else:
            ActualizarDescripcion(args.video_id)
    elif args.youtube_descripcion:
        Imprimir(f"Actualizando descripciones de Youtube desde folder")
        ActualizarDescripcionFolder()
    else:
        Imprimir("No parametro")
        data = CargarData('Comandos.json')
        Deck = MiDecks.MiDeck(data)
        CargarHilo()
