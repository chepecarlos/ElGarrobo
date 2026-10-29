"""Cambiar pagina en Dispositivo StreamDeck"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionSiguientePagina(accion):
    """Siguiente pagina en Dispositivo StreamDeck"""

    nombre = "Siguiente página"
    comando = "siguiente_pagina"
    categoria = "Folders y páginas"
    descripcion = "Pasa a la siguiente página de teclas del StreamDeck, pedal u otro dispositivo con páginas"

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

    nombre = "Página anterior"
    comando = "anterior_pagina"
    categoria = "Folders y páginas"
    descripcion = "Regresa a la página de teclas anterior del StreamDeck, pedal u otro dispositivo con páginas"

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

    nombre = "Actualizar página"
    comando = "actualizar_pagina"
    categoria = "Folders y páginas"
    descripcion = "Vuelve a dibujar los íconos de las teclas del StreamDeck"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)
