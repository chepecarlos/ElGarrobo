import json
import logging
import threading

import paho.mqtt.client as mqtt

from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__, logging.INFO)


class MiMQTT(dispositivo):

    modulo = "mqtt"
    tipo = "mqtt"
    archivoConfiguracion = "mqtt.md"

    broker: str = ""
    "Direccion del broker MQTT"
    puerto: int = 1883
    "Puerto del broker MQTT"
    cliente: mqtt.Client = None
    usuario: str = ""
    contrasenna: str = ""
    nombreControl: str = ""

    topicControl: str = ""
    nombreControl: str = ""

    def __init__(self, dataConfiguración: dict) -> None:
        """Inicializando Dispositivo de teclado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """

        super().__init__(dataConfiguración)
        self.nombre = dataConfiguración.get("nombre", "ServerMQTT")

        self.usuario: str = dataConfiguración.get("usuario", "")
        self.contrasenna: str = dataConfiguración.get("contrasenna", "")

        control = dataConfiguración.get("control", {})
        self.topicControl: str = control.get("topic", "")
        self.nombreControl: str = control.get("nombre", "")

    def conectar(self):
        """Conectar a Broker MQTT."""
        logger.info(f"MQTT[Conectando] - {self.nombre} - {self.nombreControl}")

        self.cliente = mqtt.Client(client_id=self.nombreControl)
        self.cliente.on_connect = self.EventoConectar
        self.cliente.on_disconnect = self.EventoDesconectando
        self.cliente.on_message = self.MensajeMQTT
        # TODO: re intear reconeccion

        try:
            if self.usuario is not None:
                self.cliente.username_pw_set(self.usuario, password=self.contrasenna)
            self.cliente.connect(self.dispositivo, port=self.puerto, keepalive=60)
            self.Hilo = threading.Thread(target=self.HiloServidor)
            self.Hilo.start()
            self.Conectado = True
        except Exception as error:
            logger.error(f"MQTT[Error] Dispositivo {self.nombre} no responde - {error}")
            self.Conectado = False
            # TODO intentar re-conectar después de un tiempo

    def HiloServidor(self):
        logger.info(f"MQTT[Hijo] - {self.nombre}")
        self.cliente.loop_forever()

    def EventoConectar(self, client: mqtt.Client, userdata, flags, rc):
        """Respuesta de conecion y suscripción a topicos."""
        self.Conectado = True
        logger.info(f"MQTT[Conectado] - {self.nombre}")
        if self.nombreControl and self.topicControl:
            logger.info(f"MQTT[Accion-Control] - [{self.nombreControl}]:{self.topicControl}")
            client.subscribe(self.topicControl)
            client.publish(f"{self.topicControl}/{self.nombreControl}", "conectado")

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
                logger.error(f"MQTT[Problema] Conversion a Json {Error}")
                return

            hostAccion = mensaje.get("host")

            if hostAccion == self.nombreControl or hostAccion == "todos":
                logger.info(f"MQTT[Control] - Acción({mensaje.get('accion')})")
                self.Evento(mensaje)
            else:
                logger.info("MQTT[Control] - NoConMigo")

    def EnviarMQTT(self, Topic, Mensaje):
        """Envia dato por MQTT."""
        if self.Conectado:
            self.cliente.publish(Topic, Mensaje)
        else:
            logger.error(f"MQTT[error] No Conectado con {self.nombre}")

    def Desconectar(self):
        if self.Conectado:
            logger.info("MQTT[Desconectado]")
            self.cliente.publish(f"{self.topicControl}/{self.nombreControl}", "desconectado")
            self.cliente.disconnect()
