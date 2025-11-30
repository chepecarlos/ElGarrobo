import json
import logging
import threading

import paho.mqtt.client as mqtt

from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging, SalvarValor

logger = ConfigurarLogging(__name__)


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

    listaDispositivos: list[dispositivo] = None
    "Lista de dispositivo cargados"
    listaTopicTitulo: list[str] = list()
    "Lista de Topic a escuchar para data de títulos"
    archivoTitulo: str = "data/tituloMQTT"
    "Archivo donde se guarda Titulo por mqtt"

    def __init__(self, dataConfiguración: dict) -> None:
        """Inicializando Dispositivo de teclado

        Args:
            dataConfiguración (dict): Datos de configuración del dispositivo
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
        self.cliente.on_connect = self.eventoConectar
        self.cliente.on_disconnect = self.eventoDesconectando
        self.cliente.on_message = self.mensajeMQTT
        # TODO: re intear reconeccion

        try:
            if self.usuario is not None:
                self.cliente.username_pw_set(self.usuario, password=self.contrasenna)
            self.cliente.connect(self.dispositivo, port=self.puerto, keepalive=60)
            self.Hilo = threading.Thread(target=self.HiloServidor)
            self.Hilo.start()
            self.conectado = True
        except Exception as error:
            logger.error(f"MQTT[Error] Dispositivo {self.nombre} no responde - {error}")
            self.conectado = False
            # TODO intentar re-conectar después de un tiempo

    def HiloServidor(self):
        logger.info(f"MQTT[Hijo] - {self.nombre}")
        self.cliente.loop_forever()

    def eventoConectar(self, client: mqtt.Client, userdata, flags, rc):
        """Respuesta de conecion y suscripción a topicos."""
        self.conectado = True
        logger.info(f"MQTT[Conectado] - {self.nombre}")
        if self.nombreControl and self.topicControl:
            logger.info(f"MQTT[Accion-Control] - [{self.nombreControl}]:{self.topicControl}")
            client.subscribe(self.topicControl)
            client.publish(f"{self.topicControl}/{self.nombreControl}", "conectado")
        for topic in self.listaTopicTitulo:
            logger.info(f"MQTT[Suscrito-Titulo] - {topic}")
            client.subscribe(topic)

    def eventoDesconectando(self, client, userdata, rc):
        logger.info(f"MQTT[Desconectando] - {self.nombre}")
        self.conectado = False

    def mensajeMQTT(self, client, userdata, msg):
        """Recibe mensaje por MQTT."""
        mensaje = msg.payload
        topic = msg.topic
        mensaje = str(mensaje.decode("utf-8", "ignore"))

        if topic == self.topicControl:
            logger.info(f"MQTT[{topic}] {mensaje}")
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

        if topic in self.listaTopicTitulo:
            SalvarValor(self.archivoTitulo, topic, mensaje)

            for dispositivoActual in self.listaDispositivos:
                actualizarDispositivo: bool = False
                for accionActual in dispositivoActual.listaAcciones:
                    opcionesTitulo: dict = accionActual.get("titulo_opciones")
                    if opcionesTitulo is None:
                        continue
                    topicTitulo: str = opcionesTitulo.get("mqtt")
                    if topicTitulo is not None:
                        actualizarDispositivo = True
                        break

                if actualizarDispositivo:
                    dispositivoActual.recargar = True
                    dispositivoActual.actualizar()

    def EnviarMQTT(self, Topic, Mensaje):
        """Envía dato por MQTT."""
        if self.conectado:
            self.cliente.publish(Topic, Mensaje)
        else:
            logger.error(f"MQTT[error] No Conectado con {self.nombre}")

    def desconectar(self):
        if self.conectado:
            logger.info(f"MQTT[Desconectado] - {self.nombre}")
            self.cliente.publish(f"{self.topicControl}/{self.nombreControl}", "desconectado")
            self.cliente.disconnect()

    def actualizar(self):
        if self.listaDispositivos is None:
            return

        for dispositivoActual in self.listaDispositivos:
            for accionActual in dispositivoActual.listaAcciones:
                opcionesTitulo: dict = accionActual.get("titulo_opciones")
                if opcionesTitulo is None:
                    continue
                topicTitulo: str = opcionesTitulo.get("mqtt")
                if topicTitulo is None:
                    continue

                if topicTitulo not in self.listaTopicTitulo:
                    self.listaTopicTitulo.append(topicTitulo)
                    if self.conectado:
                        self.cliente.subscribe(topicTitulo)
