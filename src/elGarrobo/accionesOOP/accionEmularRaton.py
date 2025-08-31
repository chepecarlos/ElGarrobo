"""Esperar una cantidad de tiempo"""

import time

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionDelay(accionBase):
    """Esperar una cantidad de tiempo"""

    nombre = "Ratón"
    comando = "raton"
    descripcion = "Emula el funcionamiento de ratón"

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


"""Acciones de Emulacion de teclas."""
# https://pyautogui.readthedocs.io/en/latest/install.html

import pyautogui

from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def precionarRaton(opciones):
    """Precionar boton del raton."""

    boton = opciones.get("boton", "letf")
    estado = opciones.get("estado")

    if estado is not None:
        if estado:
            pyautogui.mouseDown(button=boton)
        else:
            pyautogui.mouseUp(button=boton)
