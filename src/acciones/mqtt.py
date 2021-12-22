import json
from MiLibrerias import EnviarMensajeMQTT


def MensajeMQTT(Opciones):
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
    if "mensaje" in Opciones:
        Mensaje = Opciones["mensaje"]
    elif "opciones" in Opciones:
        Mensaje = Opciones["opciones"]
        Mensaje = json.dumps(Mensaje)

    if "topic" in Opciones:
        Topic = Opciones["topic"]

    if "usuario" in Opciones:
        Usuario = Opciones["usuario"]

    if "servidor" in Opciones:
        Servidor = Opciones["servidor"]

    if "puerto" in Opciones:
        Puerto = Opciones["puwero"]

    if "contrasenna" in Opciones:
        Contrasenna = Opciones["Contrasenna"]

    if Mensaje is not None and Topic is not None:
        EnviarMensajeMQTT(Topic, Mensaje, Usuario, Contrasenna, Servidor, Puerto)
