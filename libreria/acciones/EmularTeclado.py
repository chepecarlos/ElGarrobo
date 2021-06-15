# https://pyautogui.readthedocs.io/en/latest/install.html

import pyautogui
import pyperclip

from Extra.Delay import Delay
# Implementar press y onrelles
# TODO: Añadir ñ en las funciones
# TODO: Agregar funcionMover Raton a posicion


def ComandoTeclas(Teclas):
    for tecla in Teclas:
        pyautogui.keyDown(tecla)
    for tecla in reversed(Teclas):
        pyautogui.keyUp(tecla)


def ComandoPrecionar(Teclas, Estado=True):
    if Estado:
        for tecla in Teclas:
            pyautogui.keyDown(tecla)
    else:
        for tecla in reversed(Teclas):
            pyautogui.keyUp(tecla)


def PegarTexto(Texto):
    pyperclip.copy(Texto)
    pyautogui.hotkey('ctrl', 'v', interval=0.15)


def ComandoEscribir(Texto, Velocidad=0.01):
    pyautogui.write(Texto, interval=Velocidad)


def CopiarTexto():
    pyautogui.hotkey('ctrl', 'c')
    Delay(10)
    return pyperclip.paste()
