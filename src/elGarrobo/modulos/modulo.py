from elGarrobo.accionesOOP.heramientas.valoresAccion import valoresAcciones


class modulo:

    nombre: str
    """Nombre del módulo"""
    modulo: str
    """Identificador del módulo"""
    descripcion: str
    """Descripción del módulo"""
    archivoConfiguracion: str = ""
    """Archivo de configuración del módulo"""
    activado: bool = True
    """Indica si el módulo está activado"""

    def __init__(self, dataModulo: dict) -> None:
        pass

    def obtenerValor(self, listaValores: list[valoresAcciones], atributo: str):
        """Devuelve el valores configurado"""
        for valor in listaValores:
            if atributo == valor.atributo:
                return valor.valor

    def ejecutar(self):
        pass
