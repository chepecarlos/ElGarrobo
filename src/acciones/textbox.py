"""Acciones de Caja texto. """
import pyautogui
from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def VentanaTexto(opciones):

    Mensaje = ""
    Titulo = ""
    Defaul = ""
    Ocultar = False
    Respuesta = None
    Tipo = "string"

    if "mensaje" in opciones:
        Mensaje = opciones["mensaje"]
    if "titulo" in opciones:
        Titulo = opciones["titulo"]
    if "defaul" in opciones:
        Defaul = opciones["defaul"]
    if "ocultar" in opciones:
        Ocultar = opciones["ocultar"]
    if "tipo" in opciones:
        Tipo = opciones["tipo"]

    if Ocultar:
        Respuesta = pyautogui.password(Mensaje, Titulo, Defaul, "*")
    else:
        Respuesta = pyautogui.prompt(Mensaje, Titulo, Defaul)

    if Tipo == "entero":
        Respuesta = int(Respuesta)

    if Respuesta:
        logger.info(f"Respuesta[{Respuesta}]")
    else:
        logger.info("Respuesta[vacillo]")

    return Respuesta
