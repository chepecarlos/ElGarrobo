import logging
import paho.mqtt.client as mqtt

from MiLibrerias import ObtenerValor
from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


class MiMQTT():
    def __init__(self, Data, Evento):
        self.Conectado = False
        self.Evento = Evento
        if 'nombre' in Data:
            self.Nombre = Data['nombre']
        
        if 'broker' in Data:
            self.Broker = Data['broker']
        else:
            self.Broker = "test.mosquitto.org"
        
        if 'puerto' in Data:
            self.Puerto = Data['puerto']
        else:
            self.Puerto = 1883
        
        if 'topic' in Data:
            self.topic = Data['topic']

        if 'usuario' in Data:
            self.Usuario = Data['usuario']
        else:
            self.Usuario = None
        
        if 'contrasenna' in Data:
            self.Contrasenna = Data['contrasenna']
        else:
            self.Contrasenna = None

        self.cliente = mqtt.Client()
        self.cliente.on_connect = self.EventoConectar
        self.cliente.on_disconnect = self.EventoDesconectando
        self.cliente.on_message = self.MensajeMQTT

    def Conectar(self):
        """Conectar a Broker MQTT."""
        logger.info(f"MQTT[Conectando] - {self.Nombre}")
        if self.Usuario is not None:
            self.cliente.username_pw_set(self.Usuario, password=self.Contrasenna)
        self.cliente.connect(self.Broker, port=self.Puerto, keepalive=60)
        # self.cliente.enable_logger(logger=logging.INFO)
        self.cliente.loop_forever()

    def EventoConectar(self, client, userdata, flags, rc):
        """Respuesta de conecion y subcripcion a topicos."""
        logger.info(f"MQTT[Conectado] - {self.Nombre}")
        # logger.info("Se conecto con mqtt " + str(rc))
        self.Conectado = True
        logger.info(f"MQTT[Subcribirse] - {self.topic}")
        client.subscribe(self.topic)
    
    def EventoDesconectando(self, client, userdata, rc):
        logger.info(f"MQTT[Desconectando] - {self.Nombre}")
        self.Conectado = False

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
