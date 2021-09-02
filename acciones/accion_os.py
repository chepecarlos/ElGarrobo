"""Operaciones de Sistema Operativo."""
import os


def AccionOS(Opciones):
    """Ejecuta acciones del OS."""
    if 'comando' in Opciones:
        Comando = Opciones['comando']
        os.system(Comando)
