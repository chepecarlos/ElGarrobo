"""Accion de MQTT."""
import json
import multiprocessing

from MiLibrerias import EnviarMensajeMQTT


def mensajeMQTT(opciones):
    """
    Envia un mensaje por mqtt

    mensaje -> stl
        mensaje a enviar
    topic -> stl
        tema a publicar el mensaje
    """
    Mensaje = None
    Topic = None
    Usuario = None
    Contrasenna = None
    Servidor = None
    Puerto = None
    Esperar = None
    if "mensaje" in opciones:
        Mensaje = opciones["mensaje"]
    elif "opciones" in opciones:
        Mensaje = opciones["opciones"]
        Mensaje = json.dumps(Mensaje)

    if "topic" in opciones:
        Topic = opciones["topic"]

    if "usuario" in opciones:
        Usuario = opciones["usuario"]

    if "servidor" in opciones:
        Servidor = opciones["servidor"]

    if "puerto" in opciones:
        Puerto = opciones["puerto"]

    if "contrasenna" in opciones:
        Contrasenna = opciones["Contrasenna"]

    if "esperar" in opciones:
        Esperar = opciones["esperar"]

    if Mensaje is not None and Topic is not None:
        if Esperar is None or not Esperar:
            PSonido = multiprocessing.Process(
                target=EnviarMensajeMQTT, args=[Topic, Mensaje, Usuario, Contrasenna, Servidor, Puerto]
            )
            PSonido.start()
        else:
            EnviarMensajeMQTT(Topic, Mensaje, Usuario, Contrasenna, Servidor, Puerto)
