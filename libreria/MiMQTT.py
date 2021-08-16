"""Modulo de comunicacion con MQTT."""

# https://github.com/Elektordi/obs-websocket-py
import paho.mqtt.client as mqtt

from Extra.FuncionesArchivos import ObtenerDato

import MiLibrerias

logger = MiLibrerias.ConfigurarLogging(__name__)


class MiMQTT():
    """Clase de conexion con MQTT."""

    def __init__(self, Broker=None):
        """Inicializa coneccion con MQTT."""
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
        logger.info("Conectado a MQTT")
        self.cliente.connect(self.Broker, port=self.Puerto, keepalive=60)
        # self.cliente.enable_logger(logger=logging.INFO)
        self.cliente.loop_forever()

    def EventoConectar(self, client, userdata, flags, rc):
        """Respuesta de conecion y subcripcion a topicos."""
        logger.info("Se conecto con mqtt " + str(rc))
        client.subscribe("ALSW/#")

    def MensajeMQTT(self, client, userdata, msg):
        # """Recibe mensaje por MQTT."""
        # if msg.topic == "ALSW/temp":
        #     logger.info(f"Temperatura es {str(msg.payload)}")
        logger.info(msg.topic + " " + str(msg.payload))

    def EnviarMQTT(self, Topic, Mensaje):
        """Envia dato por MQTT."""
        self.cliente.publish(Topic, Mensaje)


def EnviarMQTTSimple(Topic, Mensaje):
    """Envia un Mensaje Simple por MQTT."""
    Usuario = ObtenerDato("/Data/MQTT.json", "Usuario")
    Contrasenna = ObtenerDato("/Data/MQTT.json", "Contrasenna")
    MiMQTTSimple = mqtt.Client()
    MiMQTTSimple.username_pw_set(Usuario, Contrasenna)
    MiMQTTSimple.connect("public.cloud.shiftr.io", 1883)
    MiMQTTSimple.publish(Topic, Mensaje)
