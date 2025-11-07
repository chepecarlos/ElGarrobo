"Clase Base que manera las propiedad y si se puede ejecución"

from pathlib import Path
from typing import Any, Callable, Optional

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerFolderConfig

from .heramientas.propiedadAccion import propiedadAccion
from .heramientas.valoresAccion import valoresAcciones

logger = ConfigurarLogging(__name__)


class accion:
    """
    clase base de las acciones del sistema
    """

    nombre: str
    "Nombre de la acción"
    comando: str
    "Identificador de la acción"
    descripcion: str
    "Descripción de la acción"
    listaPropiedades: list[propiedadAccion] = []
    "Lista Propiedad para ejecutar la acciones"
    listaValores: list[valoresAcciones] = list()
    "Valores para ejecutar la acción"
    funcion: Optional[Callable]
    "Función a ejecutarse"
    funcionExterna: Optional[Callable] = None
    "Función a ejecutarse implementada externamente"
    gui: bool = True
    "Montar acción en InterfaceWeb"
    error: bool = False
    "Error de ejecución de la acción"

    def __init__(self, nombre: str, comando: str, descripcion: str) -> None:
        """Inicializa la información de la acción hijo

        Args:
            nombre (str): Nombre de la acción
            comando (str): Identificador de la acción
            descripcion (str): Descripción de la acción
        """
        self.funcion = None
        self.nombre = nombre
        self.comando = comando
        self.descripcion = descripcion
        self.listaPropiedades: list[propiedadAccion] = []

    def agregarPropiedad(self, propiedad: propiedadAccion) -> None:
        """Agrega propiedad a la acción"""
        self.listaPropiedades.append(propiedad)

    def configurar(self, lista: dict = None) -> None:
        """Recibe la lista propiedades para ejecutar"""

        self.listaValores = list()

        if lista is None:
            return

        if isinstance(lista, dict):
            for atributo in lista:
                valor = lista[atributo]
                if not self.confirmarAtributo(atributo):
                    logger.debug(f"AcciónPOO[Error] Atributo Extra {atributo} no encontrado")
                    continue
                if self.confirmarPropiedad(atributo, valor):
                    valorActual = valoresAcciones(atributo, valor)
                    self.listaValores.append(valorActual)
                else:
                    logger.error(f"AcciónPOO[Error] Atribulo {atributo} incorrecto {type(valor)}")
                    self.error = True

    def ejecutar(self) -> bool:
        """Ejecuta la acción si es posible

        Returns:
            bool: True si se ejecutó, False si no
        """
        if not self.sePuedeEjecutar():
            logger.error(f"Acción[Error] {self.nombre} - Falta Propiedades.")
            return False

        if callable(self.funcion):
            self.funcion()
            return True

        if callable(self.funcionExterna):
            self.funcionExterna(self.listaValores)
            return True

        logger.error("AcciónPOO[Error] - Falta Función.")
        return False

    def sePuedeEjecutar(self) -> bool:
        """Confirmar que se tiene todos los atributos necesarios

        Returns:
            bool: True si se puede ejecutar, False si no
        """
        if self.error:
            return False

        valoresFaltan: list[str] = list()
        for propiedad in self.listaPropiedades:
            if propiedad.obligatorio:
                encontrado: bool = False
                for valor in self.listaValores:
                    if propiedad == valor:
                        encontrado = True
                if not encontrado:
                    valoresFaltan.append(propiedad.nombre)
        if len(valoresFaltan) > 0:
            logger.error(f"FaltaPropiedad[{self.nombre}] - {valoresFaltan}")
            return False

        return True

    def confirmarAtributo(self, atributo: str) -> bool:
        """Ver si es una propiedad esta en la lista

        Args:
            atributo (str): Atributo a buscar

        Returns:
            bool: True si existe, False si no

        """
        for propiedad in self.listaPropiedades:
            if propiedad.mismoAtributo(atributo):
                return True
        return False

    def confirmarPropiedad(self, atributo: str, valor) -> bool:
        """Ver si es una propiedad correcta

        Returns:
            bool: True si es correcta, False si no
        """
        for propiedad in self.listaPropiedades:
            if propiedad.mismoAtributo(atributo) and propiedad.mismoTipo(valor):
                return True
        return False

    def obtenerValor(self, atributo: str, default: Any = None) -> Any:
        """Devuelve el valores configurado

        Args:
            atributo (str): Atributo a buscar
        Returns:
            Any: Valor del atributo o defecto si no existe
        """
        for valor in self.listaValores:
            if atributo == valor.atributo:
                return valor.valor
        for propiedad in self.listaPropiedades:
            if atributo == propiedad.atributo:
                if propiedad.defecto is not None:
                    return propiedad.defecto

        return default

    def calcularRuta(self, ruta: str, perfil: str = "default") -> str:
        """Calcula la ruta completa a un archivo o carpeta

        Args:
            ruta (str): Ruta relativa al perfil de usuario

        Returns:
            str: Ruta completa al archivo o carpeta
        """
        folderConfig: Path = Path(ObtenerFolderConfig())
        folderPerfil: Path = folderConfig / perfil
        folderActual: Path = Path(".")
        rutaCalculada: Path = None

        folderPerfil = Path(folderConfig / folderPerfil)

        if ruta.startswith("/"):
            rutaCalculada = folderPerfil / ruta.lstrip("/")
        else:
            rutaCalculada = folderPerfil / folderActual / ruta

        return str(rutaCalculada.resolve())

    def __str__(self) -> str:
        return f"Acción: {self.nombre}[{self.atributo}]"
