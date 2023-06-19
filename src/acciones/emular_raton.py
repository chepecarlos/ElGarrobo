"""Acciones de Emulacion de teclas."""
# https://pyautogui.readthedocs.io/en/latest/install.html

import pyautogui
from MiLibrerias import ConfigurarLogging

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
