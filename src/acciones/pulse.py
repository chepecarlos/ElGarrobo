from .accion_os import AccionOS
import logging
from MiLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)

def CambiarVolumen(Opciones):

    Dispositivo = None
    Valor = None
    Opcion = "asigniar"
    comando = None

    if "dispositivo" in Opciones:
        Dispositivo = Opciones["dispositivo"]
    if "valor" in Opciones:
        Valor = Opciones["valor"]
    if "opcion" in Opciones:
        Opcion = Opciones["opcion"]

    if Dispositivo is None or Valor is None:
        logging.info("Faltan opciones")
        return

    if Opcion == "asignar":
        comando = f"pactl set-sink-volume {Dispositivo} {Valor}%"
    elif Opcion == "incremento":
        simbolo = "+" if Valor > 0 else ""
        comando = f"pactl set-sink-volume {Dispositivo} {simbolo}{Valor}%"
    else:
        logging.info("Opcion de audio no enocntrada")
        return
    
    AccionOS({"comando": comando})


def CambiarMute(Opciones):

    Dispositivo = None
    Tipo = "sink"

    if "tipo" in Opciones:
        Tipo = Opciones["tipo"]
    if "dispositivo" in Opciones:
        Dispositivo = Opciones["dispositivo"]

    if Dispositivo == None:
        Logger.info("Necesario de dispositivo")
        return

    comando = f"pactl set-{Tipo}-mute {Dispositivo} toggle"

    AccionOS({"comando": comando})
