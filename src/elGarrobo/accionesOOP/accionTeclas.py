"""Presiona una combinación de teclas"""

import pyautogui

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionTeclas(accion):
    """Presiona una combinación de teclas"""

    nombre: str = "Teclas"
    comando: str = "teclas"
    descripcion: str = "Presiona una combinación de teclas"

    propiedadTeclas: propiedadAccion = propiedadAccion(
        nombre="Teclas",
        tipo=[str, list],
        obligatorio=True,
        atributo="teclas",
        descripcion="teclas a presionar",
        ejemplo="ctrl + c",
    )
    "Propiedad para definir las teclas a presionar"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.agregarPropiedad(self.propiedadTeclas)

        self.funcion = self.presionarTeclas

    def presionarTeclas(self):
        """presiona teclas"""
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
        teclas = [str(tecla).strip().lower() for tecla in teclas]
        Logger.info(f"Teclas{teclas}")
        for tecla in teclas:
            pyautogui.keyDown(tecla)
        for tecla in reversed(teclas):
            pyautogui.keyUp(tecla)
