"""
Este es el Inicio del Código que llama a las funciones
"""

import argparse

from configurar.modulo import ConfigurarModulos
from elGarrobo.elGarrobo import elGarrobo
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerFolderConfig

logger = ConfigurarLogging(__name__)


def parametros() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="Herramientas de Macros de ALSW")
    parser.add_argument("--gui", "-g", help="Sistema interface gráfica", action="store_true")
    parser.add_argument("--configurar", "-c", help="Sistema configuración del programa", action="store_true")
    parser.add_argument("--depuracion", "-d", help="Activa la depuración", action="store_true")

    return parser.parse_args()


def configurar() -> None:
    folderConfig = ObtenerFolderConfig()
    print(folderConfig)


def main() -> None:

    logger.info("ElGarrobo[Iniciando]")
    args = parametros()
    if args.depuracion:
        logger.info("ElGarrobo[Depuración Activa]")
        logger.setLevel("DEBUG")

    if args.configurar:
        ConfigurarModulos()
    elif args.gui:
        logger.info("Iniciando la APP Gráfica")
    else:
        logger.info("ElGarrobo[sin parametros]")
        try:
            elGarrobo()
        except Exception as error:
            logger.exception(f"Error Main[{error}]")


if __name__ == "__main__":
    main()
