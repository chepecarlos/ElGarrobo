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
        try:
            if self.Usuario is not None:
                self.cliente.username_pw_set(self.Usuario, password=self.Contrasenna)
            self.cliente.connect(self.Broker, port=self.Puerto, keepalive=60)
            self.Hilo = threading.Thread(target=self.HiloServidor)
            self.Hilo.start()
            self.Conectado = True
        except Exception as error:
            logger.error(f"MQTT[Error] Dispositivo {self.Nombre} no responde")
            self.Conectado = False
            # TODO intentar re-conectar después de un tiempo

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
        Mensaje = str(Mensaje.decode("utf-8", "ignore"))
        logger.info(f"MQTT[{Topic}] {Mensaje}")

        try:
            Mensaje = json.loads(Mensaje)
        except Exception as Error:
            logger.error("MQTT[Problemas con la accion]")
            return

        if "accion" in Mensaje:
            logger.info(f"MQTT[Accion] {Mensaje['accion']}")
            self.Evento(Mensaje)

    def EnviarMQTT(self, Topic, Mensaje):
        """Envia dato por MQTT."""
        if self.Conectado:
            self.cliente.publish(Topic, Mensaje)
        else:
            logger.error(f"MQTT[error] No Conectado con {self.Nombre}")

    def Desconectar(self):
        if self.Conectado:
            logger.info("MQTT[Desconectado]")
            self.cliente.disconnect()
