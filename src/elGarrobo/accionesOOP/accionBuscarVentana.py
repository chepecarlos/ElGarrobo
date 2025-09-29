"""Esperar una cantidad de tiempo"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion
from .accionOS import accionOS

Logger = ConfigurarLogging(__name__)


class accionBuscarVentana(accion):
    """Esperar una cantidad de tiempo"""

    nombre = "Buscar Ventana"
    comando = "mostrar_ventana"
    descripcion = "Buscar ventana con un nombre"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadTitulo = {
            "nombre": "Titulo",
            "tipo": str,
            "obligatorio": True,
            "atributo": "titulo",
            "descripcion": "texto que incluye el titulo la ventana",
            "ejemplo": "obs",
        }

        self.agregarPropiedad(propiedadTitulo)

        self.funcion = self.mostarVentana

    def mostarVentana(self):
        """
        Cambia a ventana que contenga el titulo
        """
        titulo = self.obtenerValor("titulo")

        if titulo is not None:
            comando = f'xdotool search --onlyvisible "{titulo}" windowactivate'
            Logger.info(f"Buscando ventana[{titulo}]")
            accion: accion = accionOS()
            accion.configurar({"comando": comando})
            accion.ejecutar()
            # Agregar mensaje si no esta la venta
