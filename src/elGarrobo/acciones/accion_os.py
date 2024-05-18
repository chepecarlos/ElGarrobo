"""Acciones de Ejecución de Sistema Operativo."""
import os

from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def accionOS(opciones):
    """
    Ejecuta acciones del OS.

    comando -> stl
        comando a ejecutar
    """
    comando = opciones.get("comando")

    if comando is not None:
        logger.info(f"OS[{comando}]")
        os.system(comando)
