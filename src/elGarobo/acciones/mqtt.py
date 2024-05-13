"""Accion de MQTT."""
import json
import multiprocessing

from elGarobo.miLibrerias import EnviarMensajeMQTT


def mensajeMQTT(opciones):
    """
    Envia un mensaje por mqtt

    mensaje -> stl
        mensaje a enviar
    topic -> stl
        tema a publicar el mensaje
    """
    mensaje = opciones.get("mensaje")
    topic = opciones.get("topic")
    usuario = opciones.get("usuario")
    servidor = opciones.get("servidor")
    puerto = opciones.get("puerto")
    contrasenna = opciones.get("contrasenna")
    esperar = opciones.get("esperar")

    if "opciones" in opciones:
        mensaje = opciones["opciones"]
        mensaje = json.dumps(mensaje)

    if mensaje is not None and topic is not None:
        if esperar is None or not esperar:
            procesoSonido = multiprocessing.Process(
                target=EnviarMensajeMQTT,
                args=(topic, mensaje, usuario, contrasenna, servidor, puerto),
            )
            procesoSonido.start()
        else:
            EnviarMensajeMQTT(topic, mensaje, usuario, contrasenna, servidor, puerto)
