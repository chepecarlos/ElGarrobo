"""Lista de Acciones."""

from .accionDelay import accionDelay
from .accionOS import accionOS
from .accionFolder import accionFolder
from .accionTelegram import accionTelegram
from .accionControl import accionControl
from .accionNotificacion import accionNotificacion


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
    }
