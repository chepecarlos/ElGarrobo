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
    Mensaje = opciones.get("mensaje")
    Topic = opciones.get("topic")
    Usuario = opciones.get("usuario")
    Servidor = opciones.get("servidor")
    Puerto = opciones.get("puerto")
    Contrasenna = opciones.get("contrasenna")
    Esperar = opciones.get("esperar")

    if "opciones" in opciones:
        Mensaje = opciones["opciones"]
        Mensaje = json.dumps(Mensaje)

    if Mensaje is not None and Topic is not None:
        if Esperar is None or not Esperar:
            procesoSonido = multiprocessing.Process(
                target=EnviarMensajeMQTT, args=(Topic, Mensaje, Usuario, Contrasenna, Servidor, Puerto)
            )
            procesoSonido.start()
        else:
            EnviarMensajeMQTT(Topic, Mensaje, Usuario, Contrasenna, Servidor, Puerto)
