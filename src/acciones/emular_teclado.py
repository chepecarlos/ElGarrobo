"""Acciones de Emulacion de teclas."""
# https://pyautogui.readthedocs.io/en/latest/install.html

import pyautogui
import pyperclip
from MiLibrerias import ConfigurarLogging

from .delay import delay

# Implementar press y onrelles
# TODO: Añadir ñ en las funciones
# TODO: Agregar funcionMover Raton a posicion

logger = ConfigurarLogging(__name__)


def comandoTeclas(opciones):
    """
    Preciona una combinacion de tecla.

    teclas -> list
        combinaciones de teclas
    """
    if "teclas" in opciones:
        teclas = opciones["teclas"]

        logger.info(f"Teclas{teclas}")
        for tecla in teclas:
            pyautogui.keyDown(tecla)
        for tecla in reversed(teclas):
            pyautogui.keyUp(tecla)
    else:
        logger.info("Teclas[no asignadas]")


def comandoPegar(opciones):
    """
    Guarda texto en papelera.

    texto -> stl
        texto a guardas
    intervalo -> float
        tiempo de espera
    """
    if "texto" in opciones:
        texto = opciones["texto"]

        intervalo = 0.15
        if "intervalo" in opciones:
            intervalo = opciones["intervalo"]

        pyperclip.copy(texto)
        pyautogui.hotkey("ctrl", "v", interval=intervalo)


def comandoPortapapeles(opciones):
    """
    Guardar en clip un texto
    """
    if "texto" in opciones:
        texto = opciones["texto"]
        if texto is None:
            print("No Texto")
            return
        logger.info(f"Portapapeles[{texto}]")
        pyperclip.copy(texto)


def comandoEscribir(opciones):
    """
    Escribe un texto letra por letra.

    texto -> stl
        texto a guardas
    intervalo -> float
        tiempo de espera
    """
    if "texto" in opciones:
        texto = opciones["texto"]

        intervalo = 0.01
        if "intervalo" in opciones:
            intervalo = opciones["intervalo"]

        pyautogui.write(texto, interval=intervalo)


def ComandoPrecionar(opciones):
    """
    Preciona una combinacion de teclas con estado.

    tecla -> list
        combinaciones de teclas
    precionado -> bool
        estado de la tecla

    """
    estado = False
    if "teclas" in opciones:
        teclas = opciones["teclas"]
    if "precionado" in opciones:
        estado = opciones["presionado"]

    if estado:
        for tecla in teclas:
            pyautogui.keyDown(tecla)
    else:
        for tecla in reversed(teclas):
            pyautogui.keyUp(tecla)


def CopiarTexto(opciones):
    """
    Copia texto de papelera.
    """
    pyautogui.hotkey("ctrl", "c")
    Delay({"tiempo": 0.1})
    return pyperclip.paste()
