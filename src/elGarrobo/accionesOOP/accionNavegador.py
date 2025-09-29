"""Esperar una cantidad de tiempo"""

import webbrowser

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion

Logger = ConfigurarLogging(__name__)


class accionNavegador(accion):
    """Esperar una cantidad de tiempo"""

    nombre: str = "Navegador"
    comando: str = "navegador"
    descripción: str = "Abre una url en navegador preterminado"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripción)

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
        url: str = self.obtenerValor("url")

        Logger.info(f"abriendo[{url}]")
        webbrowser.open(url)
