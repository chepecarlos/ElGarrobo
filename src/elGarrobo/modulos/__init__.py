from .estadoPc import estadoPc
from .modulo import modulo
from .octoprint import moduloOctoprint
from .klipper import moduloKlipper
from .fdmMonster import moduloFdmMonster
from .obs import moduloOBS


def cargarModulos() -> list[type["modulo"]]:
    """Función para cargar los módulos disponibles"""
    listaModulos: list[type["modulo"]] = [
        estadoPc,
        moduloOctoprint,
        moduloKlipper,
        moduloFdmMonster,
        moduloOBS,
    ]
    return listaModulos
