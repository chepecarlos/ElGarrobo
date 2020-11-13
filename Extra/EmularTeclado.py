import pyautogui
# Implementar press y onrelles

def ComandoTeclas(Teclas):
    for tecla in Teclas:
        pyautogui.keyDown(tecla)
    for tecla in reversed(Teclas):
        pyautogui.keyUp(tecla)


def ComandoEscribir(Texto):
    pyautogui.write(Texto, interval=0.01)
