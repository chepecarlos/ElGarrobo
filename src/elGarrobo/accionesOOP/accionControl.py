"""Controla la PC a distancia"""

import json

from elGarrobo.miLibrerias import ConfigurarLogging, EnviarMensajeMQTT, ObtenerArchivo

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionControl(accion):
    """Controla la PC a distancia"""

    nombre = "Control MQTT"
    comando = "control"
    descripcion = "Controla la PC a distancia"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadHost = propiedadAccion(
            nombre="Host",
            tipo=str,
            obligatorio=True,
            atributo="host",
            descripcion="Computadora a controlar por MQTT",
            ejemplo="umaru",
        )

        propiedadAccionEjecutar = propiedadAccion(
            nombre="Accion",
            tipo=str,
            obligatorio=True,
            atributo="accion",
            descripcion="accion a realizar en la pc",
            ejemplo="delay",
        )

        propiedadOpciones = propiedadAccion(
            nombre="Opciones",
            tipo=dict,
            obligatorio=False,
            atributo="opciones",
            descripcion="opciones para accion a realizar en la pc",
            ejemplo="time: 1",
        )

        self.agregarPropiedad(propiedadHost)
        self.agregarPropiedad(propiedadAccionEjecutar)
        self.agregarPropiedad(propiedadOpciones)

        self.funcion = self.controlDistancia

    def controlDistancia(self):
        """espera un tiempo"""

        # TODO: usar configuraciones globales
        data = ObtenerArchivo("modulos/control/mqtt.md")

        if data is None:
            Logger.warning("No se encontró información mqtt modulos/control/mqtt.md")
            return

        self.topicControl = data.get("topic", "control")

        host = self.obtenerValor("host")
        accionHost = self.obtenerValor("accion")
        opcionesHost = self.obtenerValor("opciones")
        if host is not None and accionHost is not None:
            mensaje = {"host": host, "accion": accionHost}
            if opcionesHost:
                mensaje = {"host": host, "accion": accionHost, "opciones": opcionesHost}
                Logger.info(f"Control[{mensaje['host']}] - {mensaje['accion']}")
                Logger.info(f"Opciones: {opcionesHost}")
            else:
                mensaje = {"host": host, "accion": accionHost}
                Logger.info(f"Control[{mensaje['host']}] - {mensaje['accion']}")
            EnviarMensajeMQTT(self.topicControl, json.dumps(mensaje))
