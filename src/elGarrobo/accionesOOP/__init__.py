"""Lista de Acciones."""

from .accionControl import accionControl
from .accionDelay import accionDelay
from .accionFolder import accionFolder
from .accionNotificacion import accionNotificacion
from .accionOS import accionOS
from .accionTeclas import accionTeclas
from .accionTelegram import accionTelegram


def cargarAcciones():
    """
    Carga las acciones en una dic con nombre de accion y funcion asociada.
    """

    return {
        "delay": accionDelay,
        "os": accionOS,
        "folder": accionFolder,
        "telegram": accionTelegram,
        "control": accionControl,
        "notificacion": accionNotificacion,
        "teclas": accionTeclas,
    }
