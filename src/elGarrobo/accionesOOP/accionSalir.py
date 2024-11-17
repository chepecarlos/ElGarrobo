from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionSalir(accionBase):
    def __init__(self) -> None:
        nombre = "Salir"
        comando = "salir"
        descripcion = "Cierra el programa ElGarrobo"
        super().__init__(nombre, comando, descripcion)
