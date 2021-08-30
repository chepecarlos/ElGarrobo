# https://pyautogui.readthedocs.io/en/latest/install.html

import pyautogui
import pyperclip

from .delay import Delay
# Implementar press y onrelles
# TODO: Añadir ñ en las funciones
# TODO: Agregar funcionMover Raton a posicion


def ComandoTeclas(opciones):
    """Preciona una combinacion de tecla."""
    if 'teclas' in opciones:
        Teclas = opciones['teclas']

        for tecla in Teclas:
            pyautogui.keyDown(tecla)
        for tecla in reversed(Teclas):
            pyautogui.keyUp(tecla)


def ComandoPegar(opciones):
    """Pegar texto en papelera."""
    if 'teclas' in opciones:
        Texto = opciones['Texto']

        intervalo = 0.15
        if 'intervalo' in opciones:
            intervalo = opciones['intervalo']

        pyperclip.copy(Texto)
        pyautogui.hotkey('ctrl', 'v', interval=intervalo)


def ComandoEscribir(opciones):
    """Escribe un texto letra por letra."""
    if 'texto' in opciones:
        Texto = opciones['texto']

        intervalo = 0.01
        if 'intervalo' in opciones:
            intervalo = opciones['intervalo']

        pyautogui.write(Texto, interval=intervalo)


def ComandoPrecionar(opciones):
    """Preciona una combinacion de teclas con estado."""
    if 'teclas' in opciones:
        Teclas = opciones['teclas']
        Estado = opciones['presionado']

        if Estado:
            for tecla in Teclas:
                pyautogui.keyDown(tecla)
        else:
            for tecla in reversed(Teclas):
                pyautogui.keyUp(tecla)


def CopiarTexto():
    """Copia texto a papelera."""
    pyautogui.hotkey('ctrl', 'c')
    Delay({"tiempo": 10/1000})
    return pyperclip.paste()
