# -*- coding: utf-8 -*-

import argparse
import os
import sys

from libreria.acciones.News import SalvarArchivoNoticia
from MiLibrerias import ConfigurarLogging, SalvarValor, UnirPath

from .elgatito import ElGatito

logger = ConfigurarLogging(__name__)

if sys.version_info[0] < 3:
    logger.error("Tienes que usar Python 3 para este programa")
    os._exit(0)


def Parametros():

    parser = argparse.ArgumentParser(description="Heramientas de Macros de ALSW")
    parser.add_argument("--nodepurar", "-nd", help="Acivar modo sin depuracion", action="store_true")
    parser.add_argument("--proyecto", "-p", help="Configurar folder a proyecto actual", action="store_true")
    parser.add_argument("--news", "-n", help="Configurar folder a noticias actual")
    parser.add_argument("--striming", "-s", help="Configurar folder a noticias actual")
    parser.add_argument("--mododemo", "-dd", help="Sistema modo demo", action="store_true")
    parser.add_argument("--gui", "-g", help="Sistema interface grafica", action="store_true")

    return parser.parse_args()


def main():
    # TODO: funciones para configurar para priner aranque
    logger.info("ElGatoALSW[Iniciando]")
    args = Parametros()

    if args.proyecto:
        logger.info("Configurando Folder como Proyecto Actual")
        SalvarValor("data/proyecto.json", "ProyectoActual", os.getcwd())
    elif args.striming:
        logger.info("Configurando striming Actual")
        SalvarArchivoNoticia(args.noticias)
    elif args.news:
        logger.info("Configurar Folder de Noticias Actual")
        archivo = UnirPath(os.getcwd(), args.news)
        SalvarValor("data/news.json", "archivo", archivo)
        SalvarValor("data/news.json", "id", 0)
    elif args.mododemo:
        logger.info("Iniciando con modo Demo")
        ElGatito()
    elif args.gui:
        logger.info("Iniciando la APP Grafica")
        # gui()
    else:
        logger.info("ElGatoALSW[sin parametros]")
        try:
            ElGatito()
        except Exception as error:
            logger.exception(f"Error Main[{error}]")


if __name__ == "__main__":
    main()
