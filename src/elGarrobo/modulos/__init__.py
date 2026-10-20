from .estadoPc import estadoPc
from .modulo import modulo
from .octoprint.moduloOctoprint import moduloOctoprint
from .klipper.moduloKlipper import moduloKlipper
from .fdmMonster.moduloFdmMonster import moduloFdmMonster
from .obs.moduloOBS import moduloOBS


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
