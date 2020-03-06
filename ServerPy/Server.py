#!/usr/bin/env python3

import asyncio
import websockets
import os
from pynput.keyboard import Key, Controller

# Cargar Teclado
keyboard = Controller()

print("Activando Servidor")

def ComandoTeclas(Teclas):

    for tecla in Teclas:
        if tecla == 'ctrl':
            keyboard.press(Key.ctrl)
        elif tecla == 'alt':
            keyboard.press(Key.alt)
        elif tecla == 'shift':
            keyboard.press(Key.shift)
        elif tecla == 'super':
            keyboard.press(Key.cmd)
        elif tecla == 'f9':
            keyboard.press(Key.f9)
        elif tecla == 'f10':
            keyboard.press(Key.f10)
        else:
            keyboard.press(tecla)

    for tecla in Teclas:
        if tecla == 'ctrl':
            keyboard.release(Key.ctrl)
        elif tecla == 'alt':
            keyboard.release(Key.alt)
        elif tecla == 'shift':
            keyboard.release(Key.shift)
        elif tecla == 'super':
            keyboard.release(Key.cmd)
        elif tecla == 'f9':
            keyboard.release(Key.f9)
        elif tecla == 'f10':
            keyboard.release(Key.f10)
        else:
            keyboard.release(tecla)

async def comandoOS(websocket, path):
    comando = await websocket.recv()
    print(f"< {comando}")
    Separar = comando.split()
    Respuesta = ''
    if(Separar[0] == 'Key'):
        Separar.remove('Key')
        Respuesta = f"Teclas {Separar}"
        ComandoTeclas(Separar)
    else:
        Respuesta = f"Ejacutando {comando}!"
        os.system(comando)

    await websocket.send(Respuesta)
    print(f"> {Respuesta}")

start_server = websockets.serve(comandoOS, "Ryuk.local", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
