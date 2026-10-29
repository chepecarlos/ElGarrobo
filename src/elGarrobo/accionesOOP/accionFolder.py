"Acción que abre una ventana con nemo"

import shlex

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion
from .accionOS import accionOS

logger = ConfigurarLogging(__name__)
"@private"


class accionFolder(accion):
    "Acción que abre una ventana"

    nombre = "Abrir folder"
    comando = "folder"
    categoria = "Ventanas y sistema"
    descripcion = "Abre un folder en el explorador de archivos (Nemo)"

    propiedadRuta: propiedadAccion = propiedadAccion(
        nombre="Folder",
        tipo=str,
        obligatorio=True,
        atributo="ruta",
        descripcion="Ruta a abrir en Nemo",
        ejemplo="/home/usuario",
        ruta=True,
    )

    def __init__(self) -> None:

        super().__init__(self.nombre, self.comando, self.descripcion)

        self.agregarPropiedad(self.propiedadRuta)

        self.funcion: callable = self.abrirFolder
        "@private Función a ejecutarse"

    def abrirFolder(self):
        ruta = self.calcularRuta(self.obtenerValor("ruta"))
        logger.info(f"Abrir[{ruta}]")
        ruta = f"nemo {shlex.quote(ruta)} &"
        accion = accionOS()
        accion.configurar({"comando": ruta})
        accion.ejecutar()
