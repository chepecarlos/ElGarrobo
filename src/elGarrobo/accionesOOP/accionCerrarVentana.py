"""Acción que cierra ventana"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase
from .accionOS import accionOS

Logger = ConfigurarLogging(__name__)


class accionCerrarVentana(accionBase):
    """Cierra la ventana"""

    nombre = "Cerrar Ventana"
    comando = "cerrar_ventana"
    descripcion = "Cierra la ventana con cursor"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.funcion = self.cerrarVentana

    def cerrarVentana(self):
        """
        Activa el cerrar ventanas con el cursor
        """
        Logger.info("Selecciona programa a cerrar")

        accionCerrar = accionOS()
        accionCerrar.configurar({"comando": "xdotool selectwindow windowclose"})
        accionCerrar.ejecutar()
