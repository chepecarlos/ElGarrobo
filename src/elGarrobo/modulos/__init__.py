from .estadoPc import estadoPc
from .modulo import modulo


def cargarModulos() -> list[modulo]:
    """Función para cargar los módulos disponibles"""
    modulosDisponibles = [
        estadoPc,
    ]
    return modulosDisponibles
