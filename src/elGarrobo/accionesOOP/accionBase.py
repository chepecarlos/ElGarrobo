"Clase Base que manera las propiedad y si se puede ejecución"

from elGarrobo.miLibrerias import ConfigurarLogging

from .heramientas.propiedadAccion import propiedadAccion
from .heramientas.valoresAccion import valoresAcciones

logger = ConfigurarLogging(__name__)


class accionBase:
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
    funcion: callable = None
    "Función a ejecutarse"
    funcionExterna: callable = None
    "Función a ejecutarse implementada externamente"
    gui: bool = True
    "Montar acción en InterfaceWeb"
    error: bool = False
    "Error de ejecución de la acción"

    def __init__(self, nombre: str, comando: str, descripcion: str) -> None:
        "Inicializa la información de la acción hijo"
        self.nombre = nombre
        self.comando = comando
        self.descripcion = descripcion

    def agregarPropiedad(self, lista: dict = None) -> None:
        """Agrega propiedad a la acción"""
        nuevaPropiedad = propiedadAccion(lista)
        self.listaPropiedades.append(nuevaPropiedad)

    def configurar(self, lista: dict = None) -> None:
        """Recibe la lista propiedades para ejecutar"""

        self.listaValores = list()

        if lista is None:
            return

        if isinstance(lista, dict):
            for atributo in lista:
                valor = lista[atributo]
                if self.confirmarPropiedad(atributo, valor):
                    valorActual = valoresAcciones(atributo, valor)
                    self.listaValores.append(valorActual)
                else:
                    logger.error(f"AcciónPOO[Error] Atribulo {atributo} incorrecto {type(valor)}")
                    self.error = True

    def ejecutar(self) -> bool:
        """Ejecuta la acción si es posible"""
        if not self.sePuedeEjecutar():
            logger.error("AcciónPOO[Error] - Falta Propiedades.")
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
        """Confirmar que se tiene todos los atributos necesarios"""
        if self.error:
            return False

        listaObligatoria = []
        for propiedad in self.listaPropiedades:
            if propiedad.obligatorio:
                listaObligatoria.append(propiedad)

        if listaObligatoria:
            for propiedad in listaObligatoria:
                encontrado = False
                for valor in self.listaValores:
                    if propiedad.mismoAtributo(valor):
                        encontrado = True
                if not encontrado:
                    logger.error(f"No encontrada propiedad {propiedad.nombre}")
                    return False
        return True

    def confirmarPropiedad(self, atributo: str, valor) -> bool:
        """Ver si es una propiedad correcta"""
        for propiedad in self.listaPropiedades:
            if propiedad.mismoAtributo(atributo) and propiedad.mismoTipo(valor):
                return True
        return False

    def obtenerValor(self, atributo: str):
        """Devuelve el valores configurado"""
        for valor in self.listaValores:
            if atributo == valor.atributo:
                return valor.valor
        for propiedad in self.listaPropiedades:
            if atributo == propiedad.atributo:
                if propiedad.defecto is not None:
                    return propiedad.defecto

    def __str__(self) -> str:
        return f"Acción: {self.nombre}[{self.atributo}]"
