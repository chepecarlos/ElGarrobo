"""Cierra el programa ElGarrobo"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion

Logger = ConfigurarLogging(__name__)


class accionSalir(accion):
    """Cierra el programa ElGarrobo"""

    nombre = "Salir"
    comando = "salir"
    descripcion = "Cierra el programa ElGarrobo"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)
