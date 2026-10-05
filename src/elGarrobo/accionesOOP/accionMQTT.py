"""Acción que envía un mensaje por mqtt"""

import json
import threading
from typing import Any

import paho.mqtt.client as mqtt

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionMQTT(accion):
    """Envía un mensaje por mqtt"""

    nombre = "MQTT"
    comando = "mqtt"
    descripcion = "Envía un mensaje por mqtt"
    clientes: dict[tuple, mqtt.Client] = {}
    "Conexiones abiertas por (servidor, puerto, usuario, contraseña), se reusan entre mensajes"
    candado = threading.Lock()
    archivoData = "data/mqtt.md"
    colaDefecto = 100
    "Mensajes máximos en espera por conexión mientras no hay conexión, se cambia con 'cola' en data/mqtt.md"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadMensaje = propiedadAccion(
            nombre="Mensaje",
            tipo=[str, dict, bool],
            obligatorio=True,
            atributo="mensaje",
            descripcion="Mensaje a enviar por mqtt",
            ejemplo="Hola Mundo",
        )

        propiedadTopic = propiedadAccion(
            nombre="Topic",
            tipo=[str],
            obligatorio=True,
            atributo="topic",
            descripcion="Tema por el cual se envía el mensaje",
            ejemplo="/control/mensaje",
        )

        propiedadUsuario = propiedadAccion(
            nombre="Usuario",
            tipo=str,
            atributo="usuario",
            descripcion="Nombre del usuario para conectarse a Servidor MQTT",
            ejemplo="chepecarlos",
        )

        propiedadContraseña = propiedadAccion(
            nombre="Contraseña",
            tipo=str,
            obligatorio=False,
            atributo="contrasenna",
            descripcion="Contraseña del usuario para conectarse a Servidor MQTT",
            ejemplo="123",
        )

        propiedadServidor = propiedadAccion(
            nombre="Servidor",
            tipo=str,
            obligatorio=False,
            atributo="servidor",
            descripcion="Servidor mqtt a conectarse a Servidor MQTT",
            ejemplo="127.0.0.1",
        )

        propiedadPuerto = propiedadAccion(
            nombre="Puerto",
            tipo=int,
            obligatorio=False,
            atributo="puerto",
            descripcion="Puerto mqtt a conectarse a Servidor MQTT",
            ejemplo="8883",
        )

        self.agregarPropiedad(propiedadMensaje)
        self.agregarPropiedad(propiedadTopic)
        self.agregarPropiedad(propiedadUsuario)
        self.agregarPropiedad(propiedadContraseña)
        self.agregarPropiedad(propiedadServidor)
        self.agregarPropiedad(propiedadPuerto)

        self.funcion = self.mensajeMQTT

    @classmethod
    def obtenerCliente(cls, servidor: str, puerto: int, usuario: str, contraseña: str) -> mqtt.Client:
        """Devuelve la conexión abierta para esos datos, o la crea si no existe"""
        clave = (servidor, puerto, usuario, contraseña)
        with cls.candado:
            cliente = cls.clientes.get(clave)
            if cliente is None:
                cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                if usuario is not None and contraseña is not None:
                    cliente.username_pw_set(usuario, contraseña)
                # Si el broker está caído no acumular mensajes sin límite; los que pasen de la cola se descartan
                cola = int(ObtenerValor(cls.archivoData, "cola") or cls.colaDefecto)
                cliente.max_queued_messages_set(cola)
                # connect_async no bloquea la acción; loop_start atiende la conexión en su hilo y reconecta si se cae
                cliente.connect_async(servidor, puerto)
                cliente.loop_start()
                cls.clientes[clave] = cliente
            return cliente

    def mensajeMQTT(self):
        """Envía un mensaje por mqtt"""

        archivoData = self.archivoData
        mensaje = self.obtenerValor("mensaje")
        topic = self.obtenerValor("topic")
        usuario = self.obtenerValor("usuario") or ObtenerValor(archivoData, "usuario")
        contraseña = self.obtenerValor("contrasenna") or ObtenerValor(archivoData, "contrasenna")
        servidor = self.obtenerValor("servidor") or ObtenerValor(archivoData, "servidor")
        puerto = int(self.obtenerValor("puerto") or ObtenerValor(archivoData, "puerto") or 1883)

        if mensaje is None or topic is None:
            Logger.warning("MQTT[Falta Mensaje o topic]")
            return

        if servidor is None:
            Logger.error(f"MQTT[Falta servidor] ni en la acción ni en {archivoData}")
            return

        if isinstance(mensaje, dict):
            mensaje = json.dumps(mensaje)

        # qos=1 para que paho lo guarde y lo mande al conectar si la conexión todavía no está lista o se cayó
        self.obtenerCliente(servidor, puerto, usuario, contraseña).publish(topic, mensaje, qos=1)
