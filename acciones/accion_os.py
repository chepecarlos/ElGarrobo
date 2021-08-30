"""Operaciones de Sistema Operativo."""
import os


def AccionOS(opciones):
    """Ejecuta acciones del OS."""
    if 'comando' in opciones:
        Comando = opciones['comando']
        os.system(Comando)
