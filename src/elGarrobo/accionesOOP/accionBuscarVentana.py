from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase
from .accionOS import accionOS

Logger = ConfigurarLogging(__name__)


class accionBuscarVentana(accionBase):
    """Esperar una cantidad de tiempo"""

    def __init__(self) -> None:
        nombre = "Buscar Ventana"
        comando = "mostrar_ventana"
        descripcion = "Buscar ventana con un nombre"
        super().__init__(nombre, comando, descripcion)

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
            accion: accionBase = accionOS()
            accion.configurar({"comando": comando})
            accion.ejecutar()
            # Agregar mensaje si no esta la venta
