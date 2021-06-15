import logging
import paho.mqtt.client as mqtt

from libreria.FuncionesLogging import ConfigurarLogging

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class MiMQTT():
    """Clase de conexion con MQTT."""

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
        logger.info("Conectado a MQTT")
        self.cliente.connect(self.Broker, port=self.Puerto, keepalive=60)
        # self.cliente.enable_logger(logger=logging.INFO)
        self.cliente.loop_forever()

    def ConectarMQTT(self, client, userdata, flags, rc):
        logger.info("Se conecto con mqtt "+str(rc))
        client.subscribe("ALSW/#")

    def MensajeMQTT(self, client, userdata, msg):
        if msg.topic == "ALSW/temp":
            logger.info(f"Temperatura es {str(msg.payload)}")
        logger.info(msg.topic+" "+str(msg.payload))


# client = mqtt.Client()
# client.on_connect = on_connect
# client.on_message = on_message

# client.connect("test.mosquitto.org", 1883, 60)
