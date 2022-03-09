"""Acciones de Emulacion de teclas."""
# https://pyautogui.readthedocs.io/en/latest/install.html

import pyautogui
from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def precionarRaton(opciones):

    estado = None
    if "boton" in opciones:
        boton = opciones["boton"]
    else:
        boton = "left"

    if "estado" in opciones:
        estado = opciones["estado"]

    if estado is not None:
        if estado:
            pyautogui.mouseDown(button=boton)
        else:
            pyautogui.mouseUp(button=boton)
