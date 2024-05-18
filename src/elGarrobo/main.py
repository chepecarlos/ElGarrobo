"""
Este es el Inicio del Código que llama a las funciones
"""
import argparse
import os
import sys

from configurar.modulo import ConfigurarModulos
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerArchivo, obtenerArchivoPaquete, ObtenerFolderConfig, UnirPath

from elGarrobo.elGarrobo import elGarrobo

logger = ConfigurarLogging(__name__)

if sys.version_info[0] < 3:
    logger.error("Tienes que usar Python 3 para este programa")
    os._exit(0)


def Parametros():

    parser = argparse.ArgumentParser(description="Herramientas de Macros de ALSW")
    parser.add_argument("--gui", "-g", help="Sistema interface gráfica", action="store_true")
    parser.add_argument("--configurar", "-c", help="Sistema configuración del programa", action="store_true")

    return parser.parse_args()

def configurar() -> None:
    folderConfig = ObtenerFolderConfig()
    print(folderConfig)

def main() -> None:
    configurar();
    
    logger.info("elGarrobo[Iniciando]")
    args = Parametros()

    if args.configurar:
        ConfigurarModulos()
    elif args.gui:
        logger.info("Iniciando la APP Gráfica")
        # gui()
    else:
        logger.info("elGarrobo[sin parametros]")
        try:
            elGarrobo()
        except Exception as error:
            logger.exception(f"Error Main[{error}]")


if __name__ == "__main__":
    main()
