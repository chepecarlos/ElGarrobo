"""Acción que copiá a papelera"""

import pyautogui
import pyperclip

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase
from .accionDelay import accionDelay

Logger = ConfigurarLogging(__name__)


class accionCopiarPapelera(accionBase):
    """Copia a papeleras"""

    nombre = "Copia a papelera"
    comando = "copiar"
    descripcion = "Copia un texto a papelera"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.funcion = self.copiaTexto

    def copiaTexto(self):
        pyautogui.hotkey("ctrl", "c")

        accionEspera = accionDelay()
        accionEspera.configurar({"tiempo": 0.1})
        accionEspera.ejecutar()

        return pyperclip.paste()
