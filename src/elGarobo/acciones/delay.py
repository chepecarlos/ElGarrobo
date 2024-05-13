"""Modulo de Acciones de Tiempo."""

import time

from elGarobo.miLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


def delay(opciones):
    """
    Hace una pequeña espera en segundos.

    tiempo -> float o str
        tiempo de espera en segundos
    """

    tiempo = opciones.get("tiempo")

    if tiempo is not None:
        # TODO: confirmar que es un numero
        if isinstance(tiempo, str):
            pedadosTiempo = tiempo.split(":")
            segundos = int(pedadosTiempo[-1])
            if len(pedadosTiempo) > 1:
                segundos += int(pedadosTiempo[-2]) * 60
            if len(pedadosTiempo) > 2:
                segundos += int(pedadosTiempo[-3]) * 3600
            tiempo = segundos

        Logger.info(f"Delay[{tiempo}s]")
        time.sleep(tiempo)
