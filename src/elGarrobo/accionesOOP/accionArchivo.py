"""Escribe en un archivo la información"""

from typing import Any

from elGarrobo.miLibrerias import ConfigurarLogging, FuncionesArchivos

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionEscribirArchivo(accion):
    """Escribe en un archivo la información"""

    nombre = "Escribir Archivo"
    comando = "escribir_archivo"
    descripcion = "Escribe información en un Archivo"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadArchivo = propiedadAccion(
            nombre="Archivo",
            atributo="archivo",
            tipo=str,
            obligatorio=True,
            descripcion="Archivo a escribir la data, la ruta tiene que ser absoluta - soporta (json,md,txt)",
            ejemplo="/home/chepecarlos/archivo.json",
        )

        propiedadData = propiedadAccion(
            nombre="Archivo",
            atributo="archivo",
            tipo=Any,
            obligatorio=True,
            descripcion="Información a salvar",
            ejemplo='{"nombre": "carlos"}',
        )

        self.agregarPropiedad(propiedadArchivo)
        self.agregarPropiedad(propiedadData)

        self.funcion = self.escribirArchivo

    def escribirArchivo(self) -> None:

        archivo = self.obtenerValor("archivo")
        data = self.obtenerValor("data")

        if archivo is None or data is None:
            Logger.info("Falta información para")
            return

        FuncionesArchivos.SalvarArchivo(archivo, data)
