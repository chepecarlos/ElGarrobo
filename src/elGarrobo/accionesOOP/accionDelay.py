"""Acción para esperar un tiempo"""

import time

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionDelay(accionBase):
    """Esperar una cantidad de tiempo"""

    nombre = "Delay"
    comando = "delay"
    descripcion = "Espera una cantidad de tiempo"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadTiempo = {
            "nombre": "Tiempo",
            "tipo": str,
            "obligatorio": True,
            "atributo": "tiempo",
            "descripcion": "duración de la espera",
            "ejemplo": "1:32",
        }

        self.agregarPropiedad(propiedadTiempo)

        self.funcion = self.esperarTiempo

    def esperarTiempo(self):
        """espera un tiempo"""
        tiempo = self.obtenerValor("tiempo")
        if tiempo is None:
            Logger.error("No se dio tiempo")
            return

        if isinstance(tiempo, str):
            pedadosTiempo: str = tiempo.split(":")
            segundos: int = int(pedadosTiempo[-1])
            if len(pedadosTiempo) > 1:
                segundos += int(pedadosTiempo[-2]) * 60
            if len(pedadosTiempo) > 2:
                segundos += int(pedadosTiempo[-3]) * 3600
            tiempo = segundos

        Logger.info(f"Delay[{tiempo}s]")
        time.sleep(tiempo)
