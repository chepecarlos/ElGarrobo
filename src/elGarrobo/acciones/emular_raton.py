"""Acciones de Emulacion de teclas."""

# https://pyautogui.readthedocs.io/en/latest/install.html

import pyautogui

from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def precionarRaton(opciones):
    """Precionar boton del raton."""

    listaBotones = {"izquierdo": "left", "centro": "middle", "derecho": "right"}

    boton = opciones.get("boton", "izquierdo")
    boton = listaBotones.get(boton)
    estado = opciones.get("estado")

    if estado is not None:
        if estado:
            pyautogui.mouseDown(button=boton)
        else:
            pyautogui.mouseUp(button=boton)
