"""Acciones de texto a voz."""
# https://pypi.org/project/pyttsx3/
import pyttsx3
from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def TextoVoz(opciones):
    """
    Trasforma texto a sonido
    """
    Mensaje = None
    Volumen = 1
    Velocidad = 180
    Lenguaje = "spanish"
    Esperar = True

    if "mensaje" in opciones:
        Mensaje = opciones["mensaje"]
    if "volumen" in opciones:
        Volumen = opciones["volumen"]
    if "lenguaje" in opciones:
        Lenguaje = opciones["lenguaje"]
    if "velocidad" in opciones:
        Velocidad = opciones["velocidad"]
    if "esperar" in opciones:
        Esperar = opciones["esperar"]

    if Mensaje is None:
        logger.info("falta mensaje a reproduccir")
        return

    engine = pyttsx3.init()
    engine.setProperty("rate", Velocidad)
    engine.setProperty("volume", Volumen)
    CambiarLenguaje(engine, Lenguaje)
    logger.info(f"TextoVoz[{Mensaje}]")
    engine.say(Mensaje)
    if Esperar:
        engine.runAndWait()


def CambiarLenguaje(engine, Lenguaje):
    for voces in engine.getProperty("voices"):
        if Lenguaje in voces.name:
            engine.setProperty("voice", voces.id)
