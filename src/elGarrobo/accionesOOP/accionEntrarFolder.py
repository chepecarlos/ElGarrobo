"""Entra a un Folder y Carga las acciones por Dispositivo"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion

Logger = ConfigurarLogging(__name__)


class accionEntrarFolder(accion):
    """Entra a un Folder y Carga las acciones por Dispositivo"""

    nombre = "Entrar folder"
    comando = "entrar_folder"
    descripcion = "Entrar en un folder y cargar acciones por Dispositivo"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadFolder = {
            "nombre": "Folder",
            "tipo": str,
            "obligatorio": True,
            "atributo": "folder",
            "descripcion": "Folder a entrar",
            "ejemplo": "/blender/animar",
        }

        propiedadDispositivo = {
            "nombre": "Dispositivo",
            "tipo": str,
            "atributo": "dispositivo",
            "descripcion": "A que dispositivo a buscar las acciones",
            "ejemplo": "Teclado Manor",
        }

        self.agregarPropiedad(propiedadFolder)
        self.agregarPropiedad(propiedadDispositivo)
