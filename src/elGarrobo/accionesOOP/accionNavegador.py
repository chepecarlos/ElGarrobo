import webbrowser

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionNavegador(accionBase):
    """Esperar una cantidad de tiempo"""

    def __init__(self) -> None:
        nombre = "Navegador"
        comando = "navegador"
        descripcion = "Abre una url en navegador preterminado"
        super().__init__(nombre, comando, descripcion)

        propiedadURL = {
            "nombre": "URL",
            "tipo": str,
            "obligatorio": True,
            "atributo": "url",
            "descripcion": "direction web a abrir",
            "ejemplo": "http://google.com",
        }

        self.agregarPropiedad(propiedadURL)

        self.funcion = self.abrirNavegador

    def abrirNavegador(self):
        """espera un tiempo"""
        url = self.obtenerValor("url")

        print(f"abriendo[{url}]")
        webbrowser.open(url)
