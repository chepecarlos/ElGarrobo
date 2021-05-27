import paho.mqtt.client as mqtt


class MiMQTT():
    def __init__(self, Broker=None):
        self.cliente = mqtt.Client()
        self.cliente.on_connect = self.ConectarMQTT
        self.cliente.on_message = self.MensajeMQTT
        if Broker is not None:
            self.Broker = "test.mosquitto.org"
        else:
            self.Broker = Broker
        self.Puerto = 1883

    def Conectar(self):
        print("Conectado a MQTT")
        self.cliente.connect(self.Broker, port=self.Puerto, keepalive=60)
        # self.cliente.enable_logger(logger=logging.INFO)
        self.cliente.loop_forever()

    def ConectarMQTT(self, client, userdata, flags, rc):
        print("Se conecto con mqtt "+str(rc))
        client.subscribe("ALSW/#")

    def MensajeMQTT(self, client, userdata, msg):
        if msg.topic == "ALSW/temp":
            print(f"Temperatura es {str(msg.payload)}")
        print(msg.topic+" "+str(msg.payload))


# client = mqtt.Client()
# client.on_connect = on_connect
# client.on_message = on_message

# client.connect("test.mosquitto.org", 1883, 60)