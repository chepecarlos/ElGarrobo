"""Reinicia el proceso de ElGarrobo"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion

Logger = ConfigurarLogging(__name__)


class accionReiniciarApp(accion):
    """Reinicia el proceso de ElGarrobo"""

    nombre = "Reiniciar App"
    comando = "reiniciar_app"
    descripcion = "Reinicia el proceso de ElGarrobo"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)
