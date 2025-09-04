"""Acciones de Emulacion de teclas."""

# https://pyautogui.readthedocs.io/en/latest/install.html

import pyautogui
import pyperclip

from elGarrobo.miLibrerias import ConfigurarLogging

# from .delay import delay

# https://pyautogui.readthedocs.io/en/latest/


# Implementar press y onrelles
# TODO: Añadir ñ en las funciones
# TODO: Agregar funcionMover Raton a posicion

logger = ConfigurarLogging(__name__)


# def comandoTeclas(opciones):
#     """
#     Preciona una combinacion de tecla.

#     teclas -> list
#         combinaciones de teclas
#     """
#     teclas = opciones.get("teclas")

#     if teclas is not None:
#         logger.info(f"Teclas{teclas}")
#         for tecla in teclas:
#             pyautogui.keyDown(tecla)
#         for tecla in reversed(teclas):
#             pyautogui.keyUp(tecla)
#     else:
#         logger.info("Teclas[no asignadas]")


def comandoPegar(opciones):
    """
    Guarda texto en papelera.

    texto -> stl
        texto a guardas
    intervalo -> float
        tiempo de espera
    """
    texto = opciones.get("tecto")
    intervalo = opciones.get("intervalo", 0.15)

    if texto is not None:
        pyperclip.copy(texto)
        pyautogui.hotkey("ctrl", "v", interval=intervalo)


def comandoPortapapeles(opciones):
    """
    Guardar en clip un texto
    """
    texto = opciones.get("texto")
    if texto is not None:
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
    texto = opciones.get("texto")
    intervalo = opciones.get("intervalo", 0.01)

    if texto is not None:
        pyautogui.write(texto, interval=intervalo)


def ComandoPrecionar(opciones):
    """
    Preciona una combinacion de teclas con estado.

    tecla -> list
        combinaciones de teclas
    precionado -> bool
        estado de la tecla

    """

    teclas = opciones.get("teclas")
    estado = opciones.get("presionado")

    if estado is None or teclas is None:
        return

    if estado:
        for tecla in teclas:
            pyautogui.keyDown(tecla)
    else:
        for tecla in reversed(teclas):
            pyautogui.keyUp(tecla)


# def CopiarTexto(opciones):
#     """
#     Copia texto de papelera.
#     """
#     pyautogui.hotkey("ctrl", "c")
#     delay({"tiempo": 0.1})
#     return pyperclip.paste()
