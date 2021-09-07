"""Modulo de comunicacion con MQTT."""

# https://pypi.org/project/paho-mqtt/
import paho.mqtt.client as mqtt

from MiLibrerias import ObtenerValor
from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


class MiMQTT():
    """Clase de conexion con MQTT."""

    def __init__(self, Broker=None):
        """Inicializa coneccion con MQTT."""
        self.Conectado = False
        self.cliente = mqtt.Client()
        self.cliente.on_connect = self.EventoConectar
        self.cliente.on_message = self.MensajeMQTT
        if Broker is not None:
            self.Broker = "test.mosquitto.org"
        else:
            self.Broker = Broker
        self.Puerto = 1883

    def Conectar(self):
        """Conectar a Broker MQTT."""
        logger.info("MQTT[Conectando]")
        self.cliente.connect(self.Broker, port=self.Puerto, keepalive=60)
        # self.cliente.enable_logger(logger=logging.INFO)
        self.cliente.loop_forever()

    def EventoConectar(self, client, userdata, flags, rc):
        """Respuesta de conecion y subcripcion a topicos."""
        logger.info("MQTT[Conectado]")
        # logger.info("Se conecto con mqtt " + str(rc))
        self.Conectado = True
        client.subscribe("ALSW/#")

    def MensajeMQTT(self, client, userdata, msg):
        # """Recibe mensaje por MQTT."""
        logger.info(f"MQTT[{msg.topic}] {str(msg.payload)}")

    def EnviarMQTT(self, Topic, Mensaje):
        """Envia dato por MQTT."""
        self.cliente.publish(Topic, Mensaje)

    def Desconectar(self):
        if self.Conectado:
            logger.info("MQTT[Desconectado]")
            self.cliente.disconnect()
