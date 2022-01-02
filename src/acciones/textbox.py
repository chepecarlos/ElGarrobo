"""Acciones de Caja texto. """
import pyautogui

from acciones.accion_os import Logger


def VentanaTexto(Opciones):

    Mensaje = ""
    Titulo = ""
    Defaul = ""
    Ocultar = False
    Respuesta = None
    Tipo = "string"

    if "mensaje" in Opciones:
        Mensaje = Opciones["mensaje"]
    if "titulo" in Opciones:
        Titulo = Opciones["titulo"]
    if "defaul" in Opciones:
        Defaul = Opciones["defaul"]
    if "ocultar" in Opciones:
        Ocultar = Opciones["ocultar"]
    if "tipo" in Opciones:
        Tipo = Opciones["tipo"]

    if Ocultar:
        Respuesta = pyautogui.password(Mensaje, Titulo, Defaul, "*")
    else:
        Respuesta = pyautogui.prompt(Mensaje, Titulo, Defaul)

    if Tipo == "entero":
        Respuesta = int(Respuesta)

    if Respuesta:
        Logger.info(f"Respuesta[{Respuesta}]")
    else:
        Logger.info("Respuesta[vacillo]")

    return Respuesta
