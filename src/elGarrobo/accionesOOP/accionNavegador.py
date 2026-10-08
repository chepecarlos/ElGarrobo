"""Abre una URL en el navegador predeterminado"""

import webbrowser

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionNavegador(accion):
    """Abre una URL en el navegador predeterminado"""

    nombre: str = "Abrir navegador"
    comando: str = "navegador"
    descripción: str = "Abre una url en navegador predeterminado"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripción)

        propiedadURL = propiedadAccion(
            nombre="URL",
            tipo=str,
            obligatorio=True,
            atributo="url",
            descripcion="Dirección web a abrir",
            ejemplo="http://google.com",
        )

        self.agregarPropiedad(propiedadURL)

        self.funcion = self.abrirNavegador

    def abrirNavegador(self):
        """espera un tiempo"""
        url: str = self.obtenerValor("url")

        Logger.info(f"abriendo[{url}]")
        webbrowser.open(url)
