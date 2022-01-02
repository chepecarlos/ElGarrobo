"""Modulo de Acciones de Tiempo."""

import time

from MiLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


def Delay(Opciones):
    """
    Hace una pequeña espera en segundos.

    tiempo -> float o str
        tiempo de espera en segundos
    """

    if "tiempo" in Opciones:
        tiempo = Opciones["tiempo"]
        # TODO: confirmar que es un numero
        if isinstance(tiempo, str):
            tiempo = sum(x * int(t) for x, t in zip([3600, 60, 1], tiempo.split(":")))

        Logger.info(f"Delay[{tiempo}s]")
        time.sleep(tiempo)
