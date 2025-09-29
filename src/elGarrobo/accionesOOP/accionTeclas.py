"""Preciona una combinación de teclas"""

import pyautogui

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion

Logger = ConfigurarLogging(__name__)


class accionTeclas(accion):
    """Preciona una combinación de teclas"""

    nombre = "Teclas"
    comando = "teclas"
    descripcion = "Preciona una combinación de teclas"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadTeclas = {
            "nombre": "Teclas",
            "tipo": [str, list],
            "obligatorio": True,
            "atributo": "teclas",
            "descripcion": "teclas a presionarte",
            "ejemplo": "ctrl + c",
        }

        self.agregarPropiedad(propiedadTeclas)

        self.funcion = self.presionarTeclas

    def presionarTeclas(self):
        """preciosa teclas"""
        teclas = self.obtenerValor("teclas")

        if teclas is None:
            Logger.info("Teclas[no asignadas]")
            return

        if isinstance(teclas, str):
            listaTeclas = teclas.split("+")
            teclasEjecutar = list()
            for teclaActual in listaTeclas:
                teclasEjecutar.append(teclaActual.strip().lower())
            self.preciosaTecla(teclasEjecutar)
        elif isinstance(teclas, list):
            self.preciosaTecla(teclas)

    def preciosaTecla(self, teclas: list):
        Logger.info(f"Teclas{teclas}")
        for tecla in teclas:
            pyautogui.keyDown(tecla)
        for tecla in reversed(teclas):
            pyautogui.keyUp(tecla)
