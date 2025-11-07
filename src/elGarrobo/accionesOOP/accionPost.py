"""Realiza un consulta post para usar API"""

import requests

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionPost(accion):
    """Realiza un consulta post para usar API"""

    nombre = "Post"
    comando = "post"
    descripcion = "Realiza un consulta post para usar API"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadURL = propiedadAccion(
            nombre="url",
            tipo=str,
            obligatorio=True,
            atributo="url",
            descripcion="url a consultar",
            ejemplo="localhost",
        )

        propiedadAuth = propiedadAccion(
            nombre="auth",
            tipo=list,
            obligatorio=False,
            atributo="auth",
            descripcion="usuario  a consultar",
            ejemplo="localhost",
        )

        propiedadJson = propiedadAccion(
            nombre="JSON",
            tipo=list,
            obligatorio=False,
            atributo="json",
            descripcion="duración de la espera",
            ejemplo="1:32",
        )

        propiedadHeaders = propiedadAccion(
            nombre="headers",
            tipo=list,
            obligatorio=False,
            atributo="headers",
            descripcion="agregar cabecera a consulta",
            ejemplo="1:32",
        )

        self.agregarPropiedad(propiedadURL)
        self.agregarPropiedad(propiedadAuth)
        self.agregarPropiedad(propiedadJson)
        self.agregarPropiedad(propiedadHeaders)

        # TODO: falta implementar la accion de consulta post
