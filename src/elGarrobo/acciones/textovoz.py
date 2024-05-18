"""Acciones de texto a voz."""
# https://pypi.org/project/pyttsx3/
import pyttsx3
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def TextoVoz(opciones):
    """
    Trasforma texto a sonido
    """
    mensaje = opciones.get("mensaje")
    volumen = opciones.get("volumen", 1)
    velocidad = opciones.get('velocidad', 180)
    lenguaje = opciones.get("lenguaje", "spanish")
    esperar = opciones.get("esperar", True)


    if mensaje is None:
        logger.info("falta mensaje a reproduccir")
        return

    engine = pyttsx3.init()
    engine.setProperty("rate", velocidad)
    engine.setProperty("volume", volumen)
    CambiarLenguaje(engine, lenguaje)
    logger.info(f"TextoVoz[{mensaje}]")
    engine.say(mensaje)
    if esperar:
        engine.runAndWait()


def CambiarLenguaje(engine, lenguaje):
    for voces in engine.getProperty("voices"):
        if lenguaje in voces.name:
            engine.setProperty("voice", voces.id)
