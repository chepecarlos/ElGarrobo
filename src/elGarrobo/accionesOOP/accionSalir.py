"""Cierra el programa ElGarrobo"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionSalir(accionBase):
    """Cierra el programa ElGarrobo"""

    nombre = "Salir"
    comando = "salir"
    descripcion = "Cierra el programa ElGarrobo"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)
