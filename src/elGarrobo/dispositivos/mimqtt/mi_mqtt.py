import json
import threading

import paho.mqtt.client as mqtt

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor

logger = ConfigurarLogging(__name__)


class MiMQTT:
    def __init__(self, data, Evento):
        self.Conectado = False
        self.Evento = Evento

        self.nombre = data.get("nombre")
        self.broker = data.get("broker","test.mosquitto.org")
        self.puerto = data.get("puerto", 1883)
        self.topicControl = data.get("topic")
        self.usuario = data.get("usuario")
        self.contrasenna = data.get("contrasenna")
        self.hostControl = data.get("host", "fulanito")

        logger.info(f"MQTT[Iniciando] - {self.nombre}")
        self.cliente = mqtt.Client(client_id=self.hostControl)
        self.cliente.on_connect = self.EventoConectar
        self.cliente.on_disconnect = self.EventoDesconectando
        self.cliente.on_message = self.MensajeMQTT

    def Conectar(self):
        """Conectar a Broker MQTT."""
        logger.info(f"MQTT[Conectando] - {self.nombre} - {self.hostControl}")
        try:
            if self.usuario is not None:
                self.cliente.username_pw_set(self.usuario, password=self.contrasenna)
            self.cliente.connect(self.broker, port=self.puerto, keepalive=60)
            self.Hilo = threading.Thread(target=self.HiloServidor)
            self.Hilo.start()
            self.Conectado = True
        except Exception as error:
            logger.error(f"MQTT[Error] Dispositivo {self.nombre} no responde")
            self.Conectado = False
            # TODO intentar re-conectar después de un tiempo

    def HiloServidor(self):
        logger.info(f"MQTT[Hijo] - {self.nombre}")
        self.cliente.loop_forever()

    def EventoConectar(self, client, userdata, flags, rc):
        """Respuesta de conecion y suscripción a topicos."""
        self.Conectado = True
        logger.info(f"MQTT[Conectado] - {self.nombre}")
        if self.hostControl and self.topicControl:
            logger.info(f"MQTT[Accion-Control] - [{self.hostControl}]:{self.topicControl}")
            client.subscribe(self.topicControl)
            client.publish(f"{self.topicControl}/{self.hostControl}", "conectado")
           
    def EventoDesconectando(self, client, userdata, rc):
        logger.info(f"MQTT[Desconectando] - {self.nombre}")
        self.Conectado = False

    def MensajeMQTT(self, client, userdata, msg):
        """Recibe mensaje por MQTT."""
        mensaje = msg.payload
        topic = msg.topic
        mensaje = str(mensaje.decode("utf-8", "ignore"))
        logger.info(f"MQTT[{topic}] {mensaje}")

        if topic == self.topicControl:
            try:
                mensaje = json.loads(mensaje)
            except Exception as Error:
                logger.error("MQTT[Problema] Conversion a Json ")
                return

            hostAccion = mensaje.get("host")

            if hostAccion == self.hostControl or hostAccion == "todos":
                logger.info(f"MQTT[Control] - Acción({mensaje.get('accion')})")
                self.Evento(mensaje)
            else:
                logger.info(f"MQTT[Control] - NoConMigo")

    def EnviarMQTT(self, Topic, Mensaje):
        """Envia dato por MQTT."""
        if self.Conectado:
            self.cliente.publish(Topic, Mensaje)
        else:
            logger.error(f"MQTT[error] No Conectado con {self.nombre}")

    def Desconectar(self):
        if self.Conectado:
            logger.info("MQTT[Desconectado]")
            self.cliente.publish(f"{self.topicControl}/{self.hostControl}", "desconectado")
            self.cliente.disconnect()
