"""Operaciones de Sistema Operativo."""
import os


def AccionOS(Opciones):
    """
        Ejecuta acciones del OS.

        comando -> stl
            comando a ejecutar
    """
    if 'comando' in Opciones:
        Comando = Opciones['comando']
        os.system(Comando)
