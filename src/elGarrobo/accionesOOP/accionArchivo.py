"""Escribe en un archivo la información"""

from typing import Any

from elGarrobo.miLibrerias import ConfigurarLogging, FuncionesArchivos

from .accion import accion, propiedadAccion

logger = ConfigurarLogging(__name__)


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
            nombre="Data",
            atributo="data",
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
            logger.info("Falta información para")
            return

        FuncionesArchivos.SalvarArchivo(archivo, data)


class accionLeerValor(accion):
    """Escribe en un archivo la información"""

    nombre = "Leer Valor"
    comando = "leer_valor"
    descripcion = "Lee información en un Archivo y devuelve la data a siguiente accion"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadArchivo = propiedadAccion(
            nombre="Archivo",
            atributo="archivo",
            tipo=str,
            obligatorio=True,
            descripcion="Archivo a lee la data, la ruta tiene que ser absoluta - soporta (json,md)",
            ejemplo="/home/chepecarlos/archivo.json",
        )

        propiedadAtributo = propiedadAccion(
            nombre="Atributo",
            atributo="atributo",
            tipo=str,
            obligatorio=False,
            descripcion="Que valor leer del diccionario",
            ejemplo="nombre",
        )

        self.agregarPropiedad(propiedadArchivo)
        self.agregarPropiedad(propiedadAtributo)

        self.funcion = self.leerValor

    def leerValor(self) -> Any:
        """Lee un atributo de un archivo y lo devuelve"""
        archivo = self.obtenerValor("archivo")
        atributo = self.obtenerValor("atributo")

        data = None
        if atributo is None:
            logger.info(f"Leer[{archivo}]")
            data = FuncionesArchivos.ObtenerArchivo(archivo)
        else:
            logger.info(f"Leer[{archivo}]: {atributo}")
            data = FuncionesArchivos.ObtenerValor(archivo, atributo)
        logger.info(f"Leído[{data}]")

        return data
