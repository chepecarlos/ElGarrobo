"""Acciones de Ejecucion de Sistema Operativo."""
import os

from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def accionOS(opciones):
    """
    Ejecuta acciones del OS.

    comando -> stl
        comando a ejecutar
    """
    if "comando" in opciones:
        comando = opciones["comando"]
        logger.info(f"OS[{comando}]")
        os.system(comando)
