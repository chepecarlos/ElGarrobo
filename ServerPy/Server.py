#!/usr/bin/env python3

import os
import pyautogui
import paho.mqtt.client as mqtt

print("Activando Servidor MQTT")

def ComandoTeclas(Teclas):

    for tecla in Teclas:
        pyautogui.keyDown(tecla)

    for tecla in reversed(Teclas):
        pyautogui.keyUp(tecla)

async def comandoOS(websocket, path):
    print(f"< {comando}")
    Separar = comando.split()
    if(Separar[0] == 'Key'):
        Separar.remove('Key')
        ComandoTeclas(Separar)
    else:
        os.system(comando)

def ConectarMQTT(client, userdata, flags, rc):
    print("Conencando al Servidor - "+str(rc))
    MiMQTT.subscribe("ElGato")

def MensajeMQTT(client, userdata, msg):
    print(f"Mensaje secreto: {msg.topic} - {str(msg.payload)}")
    comando = msg.payload
    comando = comando.decode('utf-8')
    Separar = comando.split()
    if(Separar[0] == 'Key'):
        Separar.remove('Key')
        ComandoTeclas(Separar)
    else:
        os.system(comando)

def EnviandoMQTT(client, obj, mid):
    print("Mesaje: " + str(mid))

def SubcribiendoMQTT(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def LogMQTT(client, obj, level, string):
    print(f"Log: {string}")

MiMQTT = mqtt.Client()
MiMQTT.on_connect = ConectarMQTT
MiMQTT.on_publish = EnviandoMQTT
MiMQTT.on_message = MensajeMQTT
MiMQTT.on_subscribe = SubcribiendoMQTT
MiMQTT.on_log = LogMQTT

# MiMQTT.username_pw_set("ALSWSexy", "SubcribanseAALSWenYoutube")
MiMQTT.connect("ryuk.local", 1883)

MiMQTT.loop_forever()
