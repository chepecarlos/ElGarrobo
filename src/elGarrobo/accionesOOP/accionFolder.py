"Acción que abre una ventana con nemo"

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion
from .accionOS import accionOS

logger = ConfigurarLogging(__name__)
"@private"


class accionFolder(accion):
    "Acción que abre una ventana"

    nombre = "Abri Folder"
    comando = "folder"
    descripcion = "Abre un Ventana folder"

    propiedadRuta: dict = {
        "nombre": "Folder",
        "tipo": str,
        "obligatorio": True,
        "atributo": "ruta",
        "descripcion": "ruta a abri en Nemo",
        "ejemplo": "/home/usuario",
    }
    """
        Propiedad para Ejecutar la acción:
        * nombre: Folder
        * tipo: str
        * obligatorio: True
        * atributo: ruta
        * descripción: abre una ventana
        * ejemplo: /home/usuario
    """

    def __init__(self) -> None:

        super().__init__(self.nombre, self.comando, self.descripcion)

        self.agregarPropiedad(self.propiedadRuta)

        self.funcion: callable = self.abrirFolder
        "@private Función a ejecutarse"

    def abrirFolder(self):
        ruta = self.obtenerValor("ruta")
        logger.info(f"Abrir[{ruta}]")
        ruta = f"nemo {ruta} &"
        accion = accionOS()
        accion.configurar({"comando": ruta})
        accion.ejecutar()
