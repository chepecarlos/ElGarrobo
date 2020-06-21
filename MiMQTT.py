
#!/usr/bin/env python3

import os
import pyautogui
import paho.mqtt.client as mqtt


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

def MensajeMQTT(client, userdata, msg):
    print(f"Mensaje secreto: {msg.topic} - {str(msg.payload)}")

class MiMQTT(object):
    """docstring for MiMQTT."""

    def __init__(self):
        self.ConectadoMQTT = False
        self.host = "ryuk.local"
        self.port = 1883

    def CambiarHost(self, host_):
        self.host = host_

    def Conectar(self):
        try:
            self.MiMQTT = mqtt.Client()
            self.MiMQTT.on_connect = ConectarMQTT
            self.MiMQTT.on_publish = EnviandoMQTT
            self.MiMQTT.on_message = MensajeMQTT
            self.MiMQTT.on_subscribe = SubcribiendoMQTT
            self.MiMQTT.connect(self.host, self.port, 60)
            self.MiMQTT.loop_start()
            print("Termino ll")
            self.ConectadoMQTT = True
        except:
            self.ConectadoMQTT = False

    def Enviando(self, Mensaje):
        if self.ConectadoMQTT:
            self.MiMQTT.publish("ElGato", Mensaje)
        else:
            print("No conectado con MQTT")
