"""Acción que envía un mensaje por mqtt"""

import json
import multiprocessing
from multiprocessing import Value
from typing import Any

from elGarrobo.miLibrerias import ConfigurarLogging, EnviarMensajeMQTT

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionMQTT(accion):
    """Envía un mensaje por mqtt"""

    nombre = "MQTT"
    comando = "mqtt"
    descripcion = "Envía un mensaje por mqtt"
    contadorError = Value("i", 0)

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
            tipo=str,
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

    def mensajeMQTT(self):
        """Envía un mensaje por mqtt"""

        mensaje = self.obtenerValor("mensaje")
        topic = self.obtenerValor("topic")
        usuario = self.obtenerValor("usuario")
        contraseña = self.obtenerValor("contrasenna")
        servidor = self.obtenerValor("servidor")
        puerto = self.obtenerValor("puerto")

        if mensaje is None or topic is None:
            Logger.warning("MQTT[Falta Mensaje o topic]")
            return

        if isinstance(mensaje, dict):
            mensaje = json.dumps(mensaje)

        procesoSonido = multiprocessing.Process(
            target=EnviarMensajeMQTT,
            args=(
                topic,
                mensaje,
                usuario,
                contraseña,
                servidor,
                puerto,
                False,
                # accionMQTT.contadorError,
            ),
        )
        procesoSonido.start()
        # todo: error con mqtt
