"""Esperar una cantidad de tiempo"""

import pyautogui

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionEmularRaton(accionBase):
    """Esperar una cantidad de tiempo"""

    nombre = "Ratón"
    comando = "raton"
    descripcion = "Emula el funcionamiento de ratón"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadEstado = {"nombre": "Estado", "tipo": bool, "obligatorio": False, "atributo": "estado", "descripcion": "estado del boton", "ejemplo": "True", "defecto": True}

        propiedadBoton = {"nombre": "Botón", "tipo": str, "obligatorio": True, "atributo": "boton", "descripcion": "botón a presionar", "ejemplo": "izquierdo", "defecto": "izquierdo"}

        self.agregarPropiedad(propiedadEstado)
        self.agregarPropiedad(propiedadBoton)

        self.funcion = self.precionarRaton

    def precionarRaton(self):
        """Precionar boton del raton."""

        listaBotones = {"izquierdo": "left", "centro": "middle", "derecho": "right"}

        boton = self.obtenerValor("boton")
        boton = listaBotones.get(boton)
        estado = self.obtenerValor("estado")

        if estado is not None:
            if estado:
                pyautogui.mouseDown(button=boton)
            else:
                pyautogui.mouseUp(button=boton)
        else:
            Logger.warning("Falta el estado del boton")
