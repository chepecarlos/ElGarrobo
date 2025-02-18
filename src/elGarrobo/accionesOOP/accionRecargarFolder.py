from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionRecargarFolder(accionBase):
    """Sube un nivel los folder y carga las acciones por Dispositivos"""

    def __init__(self) -> None:
        nombre = "Recargar Acciones"
        comando = "reiniciar_data"
        descripcion = "Recarga las acciones desde el folder actual"
        super().__init__(nombre, comando, descripcion)

        propiedadDispositivo = {
            "nombre": "Dispositivo",
            "tipo": str,
            "atributo": "dispositivo",
            "descripcion": "A que dispositivo a buscar las acciones",
            "ejemplo": "Teclado Manor",
        }

        self.agregarPropiedad(propiedadDispositivo)
