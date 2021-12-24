import json
import multiprocessing

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
    Esperar = None
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
        Puerto = Opciones["puerto"]

    if "contrasenna" in Opciones:
        Contrasenna = Opciones["Contrasenna"]

    if "esperar" in Opciones:
        Esperar = Opciones["esperar"]

    if Mensaje is not None and Topic is not None:
        if Esperar is None or not Esperar:
            PSonido = multiprocessing.Process(
                target=EnviarMensajeMQTT, args=[Topic, Mensaje, Usuario, Contrasenna, Servidor, Puerto]
            )
            PSonido.start()
        else:
            EnviarMensajeMQTT(Topic, Mensaje, Usuario, Contrasenna, Servidor, Puerto)
