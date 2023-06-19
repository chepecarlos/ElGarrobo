"""Lista de Acciones."""

from .accionDelay import accionDelay
from .accionOS import accionOS


def cargarAcciones():
    """
    Carga las acciones en una dic con nombre de accion y funcion asociada.
    """

    return {
        "delay": accionDelay,
        "os": accionOS
        }
