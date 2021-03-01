#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Librerias
import os
import argparse
import sys
import Extra.MiDeck as MiDecks
import logging


# Cargar funciones de Archivos
from Extra.FuncionesProyecto import SalvarProyecto, CargarProyecto, CargarIdVideo, CrearFolderProyecto
from Extra.News import SalvarArchivoNoticia
from Extra.Depuracion import Imprimir, CambiarDepuracion
from Extra.YoutubeChat import SalvarChatYoutube
from Extra.CargarData import CargarData
from Extra.Hilos import CargarHilo
from Extra.FuncionesBlender import CrearProxy, RenderizarVideo, BorrarTemporalesBender
from Extra.ApiYoutube import ActualizarDescripcion, ActualizarThumbnails, ActualizarDescripcionFolder

from libreria.ElGatito import ElGatito
from libreria.FuncionesArchivos import ObtenerArchivo
from libreria.FuncionesLogging import ConfigurarLogging, NivelLogging

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)

parser = argparse.ArgumentParser(description='Heramienta de creacion de contenido de ALSW')
parser.add_argument('--nodepurar', '-nd', help="Acivar modo sin depuracion", action="store_true")
parser.add_argument('--proyecto', '-p', help="Configurar folder a proyecto actual", action="store_true")
parser.add_argument('--noticias', '-n', help="Configurar folder a noticias actual")
parser.add_argument('--salvaryoutube', '-sy', help="Salva el chat en un archivo", action="store_true")
parser.add_argument('--mododemo', '-dd', help="Sistema modo demo",  action="store_true")
parser.add_argument('--blenderproxy', '-bp', help="Creando proxy de Blender",  action="store_true")
parser.add_argument('--blenderrenderizar', '-br', help="Empezando a Renderizar Video")
parser.add_argument('--blenderborrar', '-bb', help="Borrar Temporales", action="store_true")
parser.add_argument('--folderproyecto', '-fp', help="Creando folder proyecto de video")

parser.add_argument('--video-thumbnails', '-vt', help="Archivo de Thumbnails  en Youtube",  action="store_true")
parser.add_argument("--video-descripcion", '-vd', help="ID del video a actualizar descripcipn en Youtube",  action="store_true")

parser.add_argument('--video-id', '-vi', help="ID del video a actualizar Youtube")
parser.add_argument('--video-file', '-vf', help="Archivo a usar para actualizar Youtube")
parser.add_argument('--video-recursivo', '-vr', help="Archivo a usar para actualizar Youtube")


if sys.version_info[0] < 3:
    logger.error("Tienes que usar Python 3 para este programa")
    sys.exit(1)

# Principal
if __name__ == "__main__":
    # TODO: funciones para configurar para priner aranque
    logger.info("Iniciando el programa ElGatoALSW")
    args = parser.parse_args()

    if args.nodepurar:
        CambiarDepuracion(False)
        NivelLogging(logging.WARNING)

    if args.proyecto:
        Imprimir("Configurando Folder como Proyecto Actual")
        SalvarProyecto(os.getcwd())
    elif args.noticias:
        Imprimir("Configurar Folder para Noticias Actual")
        SalvarArchivoNoticia(os.getcwd() + "/" + args.noticias)
    elif args.salvaryoutube:
        Imprimir("Emezandoa a guardar Chat en Proyecto Actual")
        SalvarChatYoutube(CargarProyecto(), CargarIdVideo())
    elif args.mododemo:
        logger.info("Iniciando con modo Demo")
        # TODO Cargar informacion desde #HOME/.config/ElGATOALSW
        data = ObtenerArchivo('config.json')
        ElGatito(data)
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
    elif args.video_descripcion:
        if args.video_id:
            Imprimir(f"Actualizando descripcion del Video {args.video_id}")
            if args.video_file:
                ActualizarDescripcion(args.video_id, args.video_file)
            else:
                ActualizarDescripcion(args.video_id)
        elif args.video_recursivo:
            Imprimir(f"Actualizando descripciones de Youtube desde folder")
            ActualizarDescripcionFolder()
        else:
            Imprimir("Falta el ID del video")
    elif args.video_thumbnails:
        if args.video_id:
            Imprimir(f"Actualizando Thumbnails del Video {args.video_id}")
            if args.video_file:
                ActualizarThumbnails(args.video_id, args.video_file)
            else:
                ActualizarThumbnails(args.video_id)
        else:
            Imprimir("Falta el ID del video")
    else:
        logger.info("Iniciando sin parametros")
        data = CargarData('Comandos.json')
        Deck = MiDecks.MiDeck(data)
        CargarHilo()
