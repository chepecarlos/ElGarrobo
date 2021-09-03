"""Modulo de Tiempo."""
import MiLibrerias
import time

from MiLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


def Delay(Opciones):
    """
        Hace una pequeña espera en segundos.

        tiempo -> float 
            tiempo de espera en segundos
    """
    if 'tiempo' in Opciones:
        tiempo = Opciones['tiempo']
        Logger.info(f"Emperando {tiempo}")
        time.sleep(tiempo)
