#!/usr/bin/env python3

import asyncio
import websockets
import os
import pyautogui

# Cargar Teclado
keyboard = Controller()

print("Activando Servidor")

def ComandoTeclas(Teclas):

    for tecla in Teclas:
        pyautogui.keyDown(tecla)

    for tecla in reversed(Teclas):
        pyautogui.keyUp(tecla)

async def comandoOS(websocket, path):
    comando = await websocket.recv()
    print(f"< {comando}")
    Separar = comando.split()
    if(Separar[0] == 'Key'):
        Separar.remove('Key')
        ComandoTeclas(Separar)
    else:
        os.system(comando)
    # await websocket.send(Respuesta)
    print(f"> {Respuesta}")

start_server = websockets.serve(comandoOS, "ryuk.local", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
