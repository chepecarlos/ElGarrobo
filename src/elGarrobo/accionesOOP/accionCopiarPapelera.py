"""Acciones para copiar y pegar usando el portapapeles"""

import pyautogui
import pyperclip

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion
from .accionDelay import accionDelay

Logger = ConfigurarLogging(__name__)


class accionCopiarPapelera(accion):
    """Copia al portapapeles"""

    nombre = "Copiar al portapapeles"
    comando = "copiar"
    descripcion = "Copia el texto seleccionado al portapapeles"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.funcion = self.copiaTexto

    def copiaTexto(self):
        pyautogui.hotkey("ctrl", "c")

        accionEspera = accionDelay()
        accionEspera.configurar({"tiempo": 0.1})
        accionEspera.ejecutar()

        return pyperclip.paste()


class accionPegarTexto(accion):
    """Pega un texto usando el portapapeles"""

    nombre = "Pegar texto"
    comando = "pegar"
    descripcion = "Copia un texto al portapapeles y lo pega con ctrl+v"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadTexto = propiedadAccion(
            nombre="Texto",
            atributo="texto",
            tipo=[str],
            multilinea=True,
            obligatorio=True,
            descripcion="texto a pegar",
            ejemplo="Hola mundo",
        )

        self.agregarPropiedad(propiedadTexto)

        self.funcion = self.pegarTexto

    def pegarTexto(self):
        """Pega un texto"""
        texto = self.obtenerValor("texto")
        pyperclip.copy(texto)
        pyautogui.hotkey("ctrl", "v")
        Logger.info(f"Pegando[{texto}]")
