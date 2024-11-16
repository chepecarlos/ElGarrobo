"""Lista de Acciones."""

from .accionControl import accionControl
from .accionDelay import accionDelay
from .accionFolder import accionFolder
from .accionMQTT import accionMQTT
from .accionNotificacion import accionNotificacion
from .accionOS import accionOS
from .accionTeclas import accionTeclas
from .accionTelegram import accionTelegram


def cargarAcciones():
    """
    Carga las acciones en una dic con nombre de accion y función asociada.
    """

    return {
        "control": accionControl,
        "delay": accionDelay,
        "folder": accionFolder,
        "mqtt": accionMQTT,
        "notificacion": accionNotificacion,
        "os": accionOS,
        "teclas": accionTeclas,
        "telegram": accionTelegram,
    }
