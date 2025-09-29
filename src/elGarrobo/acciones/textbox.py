"""Acciones de Caja texto."""

import pyautogui

from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def VentanaTexto(opciones):

    mensaje = opciones.get("mensaje")
    titulo = opciones.get("titulo")
    default = opciones.get("default")
    ocultar = opciones.get("ocultar", False)
    tipo = opciones.get("tipo", "string")
    respuesta = None

    if ocultar:
        respuesta = pyautogui.password(mensaje, titulo, default, "*")
    else:
        respuesta = pyautogui.prompt(mensaje, titulo, default)

    if tipo == "entero":
        respuesta = int(respuesta)

    if respuesta:
        logger.info(f"Respuesta[{respuesta}]")
    else:
        logger.info("Respuesta[vacillo]")

    return respuesta
