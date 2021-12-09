import pyttsx3

from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def TextoVoz(Opciones):
    """
    Trasforma texto a sonido
    """
    Mensaje = None
    Volumen = 1
    Velocidad = 180
    Lenguaje = "spanish"
    Esperar = True

    if "mensaje" in Opciones:
        Mensaje = Opciones["mensaje"]
    if "volumen" in Opciones:
        Volumen = Opciones["volumen"]
    if "lenguaje" in Opciones:
        Lenguaje = Opciones["lenguaje"]
    if "velocidad" in Opciones:
        Velocidad = Opciones["velocidad"]
    if "esperar" in Opciones:
        Esperar = Opciones["esperar"]

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
