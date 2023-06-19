"""Lista de Acciones."""

from .accionDelay import accionDelay


def cargarAcciones():
    """
    Carga las acciones en una dic con nombre de accion y funcion asociada.
    """

    return {
        "delay": accionDelay
        }
