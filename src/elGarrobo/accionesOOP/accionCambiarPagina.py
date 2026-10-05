"""Cambiar pagina en Dispositivo StreamDeck"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionSiquientePagina(accion):
    """Siguiente pagina en Dispositivo StreamDeck"""

    nombre = "Siguiente Pagina"
    comando = "siquiente_pagina"
    descripcion = "Siguiente pagina en Dispositivos StreamDeck"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadDispositivo = propiedadAccion(
            nombre="Dispositivo",
            tipo=str,
            atributo="dispositivo",
            descripcion="Dispositivo a cambiar de página; vacío cambia todos los que tienen página global",
            ejemplo="pedal",
        )
        self.agregarPropiedad(propiedadDispositivo)


class accionAnteriorPagina(accion):
    """Anterior pagina en Dispositivo StreamDeck"""

    nombre = "Anterior Pagina"
    comando = "anterior_pagina"
    descripcion = "Anterior pagina en Dispositivos StreamDeck"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadDispositivo = propiedadAccion(
            nombre="Dispositivo",
            tipo=str,
            atributo="dispositivo",
            descripcion="Dispositivo a cambiar de página; vacío cambia todos los que tienen página global",
            ejemplo="pedal",
        )
        self.agregarPropiedad(propiedadDispositivo)


class accionActualizarPagina(accion):
    """Actualiza pagina de  StreamDeck"""

    nombre = "Actualiza Pagina"
    comando = "actualizar_pagina"
    descripcion = "Actualiza pagina en Dispositivos StreamDeck"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)
