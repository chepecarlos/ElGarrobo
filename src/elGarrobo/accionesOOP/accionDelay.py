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

    esperarSegundos: int | str = 0

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
        self.esperaSegundos = self.obtenerValor("tiempo")
        if self.esperaSegundos is None:
            Logger.error("Falta tiempo")
            return

        if isinstance(self.esperaSegundos, str):
            pedadosTiempo: list[str] = self.esperaSegundos.split(":")
            segundos: int = int(pedadosTiempo[-1])
            if len(pedadosTiempo) > 1:
                segundos += int(pedadosTiempo[-2]) * 60
            if len(pedadosTiempo) > 2:
                segundos += int(pedadosTiempo[-3]) * 3600
            self.esperaSegundos = segundos

        Logger.info(f"Delay[{self.esperaSegundos}s]")
        time.sleep(self.esperaSegundos)
