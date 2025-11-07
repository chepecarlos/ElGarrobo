"""Acción para esperar un tiempo"""

import time

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

# from .heramientas.propiedadAccion import propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionDelay(accion):
    """Esperar una cantidad de tiempo"""

    nombre = "Delay"
    comando = "delay"
    descripcion = "Espera una cantidad de tiempo"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadTiempo = propiedadAccion(
            nombre="Tiempo",
            atributo="tiempo",
            tipo=[int, str],
            obligatorio=True,
            descripcion="duración de la espera en segundos",
            ejemplo="1:32",
        )

        self.agregarPropiedad(propiedadTiempo)

        self.funcion = self.esperarTiempo

    def esperarTiempo(self):
        """espera un tiempo"""
        esperaSegundos = self.obtenerValor("tiempo")
        if esperaSegundos is None:
            Logger.error("Falta tiempo")
            return

        if isinstance(esperaSegundos, str):
            pedadosTiempo: str = esperaSegundos.split(":")
            segundos: int = int(pedadosTiempo[-1])
            if len(pedadosTiempo) > 1:
                segundos += int(pedadosTiempo[-2]) * 60
            if len(pedadosTiempo) > 2:
                segundos += int(pedadosTiempo[-3]) * 3600
            esperaSegundos = segundos

        Logger.info(f"Delay[{esperaSegundos}s]")
        time.sleep(esperaSegundos)
