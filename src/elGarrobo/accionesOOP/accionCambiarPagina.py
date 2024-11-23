import time

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionSiquientePagina(accionBase):
    """Siguiente pagina en Dispositivo StreamDeck"""

    def __init__(self) -> None:
        nombre = "Siguiente Pagina"
        comando = "siquiente_pagina"
        descripcion = "Siguiente pagina en Dispositivos StreamDeck"
        super().__init__(nombre, comando, descripcion)


class accionAnteriorPagina(accionBase):
    """Anterior pagina en Dispositivo StreamDeck"""

    def __init__(self) -> None:
        nombre = "Anterior Pagina"
        comando = "anterior_pagina"
        descripcion = "Anterior pagina en Dispositivos StreamDeck"
        super().__init__(nombre, comando, descripcion)


class accionActualizarPagina(accionBase):
    """Actualiza pagina de  StreamDeck"""

    def __init__(self) -> None:
        nombre = "Actualiza Pagina"
        comando = "actualizar_pagina"
        descripcion = "Actualiza pagina en Dispositivos StreamDeck"
        super().__init__(nombre, comando, descripcion)
