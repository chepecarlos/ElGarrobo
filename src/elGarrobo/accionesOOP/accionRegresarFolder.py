"""Sube un nivel los folder y carga las acciones por Dispositivos"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionRegresarFolder(accion):
    """Sube un nivel los folder y carga las acciones por Dispositivos"""

    nombre = "Regresar Folder"
    comando = "regresar_folder"
    descripcion = "Sube un nivel los folder y carga las acciones por Dispositivos"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadDispositivo = propiedadAccion(
            nombre="Dispositivo",
            tipo=str,
            atributo="dispositivo",
            descripcion="A que dispositivo a buscar las acciones",
            ejemplo="Teclado Manor",
        )

        self.agregarPropiedad(propiedadDispositivo)
