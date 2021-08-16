#!/home/chepecarlos/5.Programas/2.Heramientas/1.ElGatoALSW/venv/bin/python
#/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

from Extra.FuncionesProyecto import (CargarIdVideo, CargarProyecto,
                                     CrearFolderProyecto, SalvarProyecto)
from Extra.YoutubeChat import SalvarChatYoutube
from libreria.acciones.News import SalvarArchivoNoticia
from libreria.ElGatito import ElGatito
from libreria.FuncionesArchivos import ObtenerArchivo, SalvarValor, UnirPath

import MiLibrerias

logger = MiLibrerias.ConfigurarLogging(__name__)

if sys.version_info[0] < 3:
    logger.error("Tienes que usar Python 3 para este programa")
    os._exit(0)

def Parametros():

    parser = argparse.ArgumentParser(description='Heramienta de creacion de contenido de ALSW')
    parser.add_argument('--nodepurar', '-nd', help="Acivar modo sin depuracion", action="store_true")
    parser.add_argument('--proyecto', '-p', help="Configurar folder a proyecto actual", action="store_true")
    parser.add_argument('--news', '-n', help="Configurar folder a noticias actual")
    parser.add_argument('--striming', '-s', help="Configurar folder a noticias actual")
    parser.add_argument('--salvaryoutube', '-sy', help="Salva el chat en un archivo", action="store_true")
    parser.add_argument('--mododemo', '-dd', help="Sistema modo demo", action="store_true")
    parser.add_argument('--gui', '-g', help="Sistema interface grafica", action="store_true")
    parser.add_argument('--blenderproxy', '-bp', help="Creando proxy de Blender", action="store_true")
    parser.add_argument('--blenderrenderizar', '-br', help="Empezando a Renderizar Video")
    parser.add_argument('--blenderborrar', '-bb', help="Borrar Temporales", action="store_true")
    parser.add_argument('--folderproyecto', '-fp', help="Creando folder proyecto de video")

    return parser.parse_args()

def main():
    # TODO: funciones para configurar para priner aranque
    logger.info("Iniciando el programa ElGatoALSW")
    args = Parametros()

    if args.proyecto:
        logger.info("Configurando Folder como Proyecto Actual")
        SalvarProyecto(os.getcwd())
    elif args.striming:
        logger.info("Configurando striming Actual")
        SalvarArchivoNoticia(args.noticias)
    elif args.news:
        logger.info("Configurar Folder de Noticias Actual")
        archivo = UnirPath(os.getcwd(), args.news)
        SalvarValor("data/news.json", "archivo", archivo)
        SalvarValor("data/news.json", "id", 0)
        pass
    elif args.salvaryoutube:
        logger.info(f"Emezandoa a guardar Chat en Proyecto Actual {CargarProyecto()} {CargarIdVideo()}")
        SalvarChatYoutube(CargarProyecto(), CargarIdVideo())
    elif args.mododemo:
        logger.info("Iniciando con modo Demo")
        ElGatito()
    elif args.gui:
        logger.info("Iniciando la APP Grafica")
        # gui()
    elif args.folderproyecto:
        logger.info(f"Creando folder de Proyecto {args.folderproyecto}")
        CrearFolderProyecto(args.folderproyecto)
    else:
        logger.info("Iniciando sin parametros")
        ElGatito()

if __name__ == "__main__":
    main()
