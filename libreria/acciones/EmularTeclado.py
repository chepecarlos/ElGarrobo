# https://pyautogui.readthedocs.io/en/latest/install.html

import pyautogui
import pyperclip

from libreria.acciones import Delay
# Implementar press y onrelles
# TODO: Añadir ñ en las funciones
# TODO: Agregar funcionMover Raton a posicion


def ComandoTeclas(Teclas):
    """Preciona una combinacion de tecla."""
    for tecla in Teclas:
        pyautogui.keyDown(tecla)
    for tecla in reversed(Teclas):
        pyautogui.keyUp(tecla)


def ComandoPrecionar(Teclas, Estado=True):
    """Preciona una combinacion de teclas con estado."""
    if Estado:
        for tecla in Teclas:
            pyautogui.keyDown(tecla)
    else:
        for tecla in reversed(Teclas):
            pyautogui.keyUp(tecla)


def PegarTexto(Texto):
    """Pegar texto en papelera."""
    pyperclip.copy(Texto)
    pyautogui.hotkey('ctrl', 'v', interval=0.15)


def ComandoEscribir(Texto, Velocidad=0.01):
    """Escribe un texto letra por letra."""
    pyautogui.write(Texto, interval=Velocidad)


def CopiarTexto():
    """Copia texto a papelera."""
    pyautogui.hotkey('ctrl', 'c')
    Delay(10/1000)
    return pyperclip.paste()
