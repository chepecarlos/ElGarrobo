from .accionBase import accionBase
from MiLibrerias import ConfigurarLogging
from .accionOS import accionOS

logger = ConfigurarLogging(__name__)


class accionFolder(accionBase):
    def __init__(self) -> None:
        nombre = "Abir Folder"
        comando = "folder"
        descripcion = "Abre un folder"
        super().__init__(nombre, comando, descripcion)

        propiedadTiempo = {
            "nombre": "Folder",
            "tipo": str,
            "obligatorio": True,
            "atributo": "ruta",
            "descripcion": "comando de bash",
            "ejemplo": "/home/usuario",
        }

        self.agregarPropiedad(propiedadTiempo)

        self.funcion = self.abrirFolder

    def abrirFolder(self):
        ruta = self.obtenerValor("ruta")
        logger.info(f"Abrir[{ruta}]")
        ruta = f"nemo {ruta} &"
        accion = accionOS()
        accion.configurar({"comando": ruta})
        accion.ejecutar()
