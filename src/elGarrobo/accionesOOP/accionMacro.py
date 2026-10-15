"""Ejecuta una lista de acciones una tras otra"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionMacro(accion):
    """Ejecuta una lista de acciones una tras otra, pasando datos entre pasos con el cajón"""

    nombre = "Macro"
    comando = "macro"
    descripcion = "Ejecuta una lista de acciones una tras otra"
    atributoLista = "acciones"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadAcciones = propiedadAccion(
            nombre="Acciones",
            tipo=list,
            obligatorio=True,
            atributo="acciones",
            descripcion="Lista de acciones a ejecutar en orden",
            ejemplo="- accion: delay\n  opciones:\n    tiempo: 1",
        )

        self.agregarPropiedad(propiedadAcciones)
