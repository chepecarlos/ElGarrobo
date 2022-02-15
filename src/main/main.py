# -*- coding: utf-8 -*-

import argparse
import os
import sys

from configurar.modulo import ConfigurarModulos
from MiLibrerias import ConfigurarLogging

from .elgatito import ElGatito

logger = ConfigurarLogging(__name__)

if sys.version_info[0] < 3:
    logger.error("Tienes que usar Python 3 para este programa")
    os._exit(0)


def Parametros():

    parser = argparse.ArgumentParser(description="Herramientas de Macros de ALSW")
    parser.add_argument("--gui", "-g", help="Sistema interface grafica", action="store_true")
    parser.add_argument("--configurar", "-c", help="Sistema configuración del programa", action="store_true")

    return parser.parse_args()


def main():
    logger.info("ElGatoALSW[Iniciando]")
    args = Parametros()

    if args.configurar:
        ConfigurarModulos()
    elif args.gui:
        logger.info("Iniciando la APP Gráfica")
        # gui()
    else:
        logger.info("ElGatoALSW[sin parametros]")
        try:
            ElGatito()
        except Exception as error:
            logger.exception(f"Error Main[{error}]")


if __name__ == "__main__":
    main()
