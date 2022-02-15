import json
import threading

import paho.mqtt.client as mqtt
from MiLibrerias import ConfigurarLogging, ObtenerValor

logger = ConfigurarLogging(__name__)


class MiMQTT:
    def __init__(self, Data, Evento):
        self.Conectado = False
        self.Evento = Evento
        if "nombre" in Data:
            self.Nombre = Data["nombre"]

        if "broker" in Data:
            self.Broker = Data["broker"]
        else:
            self.Broker = "test.mosquitto.org"

        if "puerto" in Data:
            self.Puerto = Data["puerto"]
        else:
            self.Puerto = 1883

        if "topic" in Data:
            self.topic = Data["topic"]

        if "usuario" in Data:
            self.Usuario = Data["usuario"]
        else:
            self.Usuario = None

        if "contrasenna" in Data:
            self.Contrasenna = Data["contrasenna"]
        else:
            self.Contrasenna = None

        logger.info(f"MQTT[Iniciando] - {self.Nombre}")
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
        self.Hilo = threading.Thread(target=self.HiloServidor)
        self.Hilo.start()

    def HiloServidor(self):
        logger.info(f"MQTT[Hijo] - {self.Nombre}")
        self.cliente.loop_forever()

    def EventoConectar(self, client, userdata, flags, rc):
        """Respuesta de conecion y suscripción a topicos."""
        self.Conectado = True
        logger.info(f"MQTT[Conectado] - {self.Nombre}")
        logger.info(f"MQTT[Sub] - [{self.Nombre}]:{self.topic}")
        client.subscribe(self.topic)

    def EventoDesconectando(self, client, userdata, rc):
        logger.info(f"MQTT[Desconectando] - {self.Nombre}")
        self.Conectado = False

    def MensajeMQTT(self, client, userdata, msg):
        """Recibe mensaje por MQTT."""
        Mensaje = msg.payload
        Topic = msg.topic
        logger.info(f"MQTT[{Topic}] {str(Mensaje)}")
        Mensaje = str(Mensaje.decode("utf-8", "ignore"))
        Mensaje = json.loads(Mensaje)
        if "accion" in Mensaje:
            logger.info(f"MQTT[Accion] {Mensaje['accion']}")
            self.Evento(Mensaje)

    def EnviarMQTT(self, Topic, Mensaje):
        """Envia dato por MQTT."""
        self.cliente.publish(Topic, Mensaje)

    def Desconectar(self):
        if self.Conectado:
            logger.info("MQTT[Desconectado]")
            self.cliente.disconnect()
