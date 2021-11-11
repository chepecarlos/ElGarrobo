"""Operaciones de Sistema Operativo."""
import os
from MiLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)

def AccionOS(Opciones):
    """
    Ejecuta acciones del OS.

    comando -> stl
        comando a ejecutar
    """
    if "comando" in Opciones:
        Comando = Opciones["comando"]
        Logger.info(f"OS[{Comando}]")
        os.system(Comando)
