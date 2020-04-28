import pyautogui

def ComandoTeclas(Teclas):
    for tecla in Teclas:
        pyautogui.keyDown(tecla)
    for tecla in reversed(Teclas):
        pyautogui.keyUp(tecla)
