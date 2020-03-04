#!/usr/bin/env python3

import asyncio
import websockets
import os

print("Activando Servidor")

async def comandoOS(websocket, path):
    comando = await websocket.recv()
    print(f"< {comando}")

    os.system(comando)

    Respuesta = f"Ejacutando {comando}!"

    await websocket.send(Respuesta)
    print(f"> {Respuesta}")

start_server = websockets.serve(comandoOS, "Ryuk.local", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
