from .estadoPc import estadoPc
from .modulo import modulo
from .estadoOctoprint import estadoOctoprint


def cargarModulos() -> list[type["modulo"]]:
    """Función para cargar los módulos disponibles"""
    listaModulos: list[type["modulo"]] = [
        estadoPc,
        estadoOctoprint,
    ]
    return listaModulos
