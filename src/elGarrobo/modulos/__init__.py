from .estadoPc import estadoPc
from .modulo import modulo
from .estadoOctoprint import estadoOctoprint
from .estadoKlipper import estadoKlipper


def cargarModulos() -> list[type["modulo"]]:
    """Función para cargar los módulos disponibles"""
    listaModulos: list[type["modulo"]] = [
        estadoPc,
        estadoOctoprint,
        estadoKlipper,
    ]
    return listaModulos
