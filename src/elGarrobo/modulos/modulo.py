from elGarrobo.accionesOOP.heramientas.valoresAccion import valoresAcciones


class modulo:

    nombre: str
    modulo: str
    descripcion: str

    def __init__(self):
        pass

    def obtenerValor(self, listaValores: list[valoresAcciones], atributo: str):
        """Devuelve el valores configurado"""
        for valor in listaValores:
            if atributo == valor.atributo:
                return valor.valor

    def ejecutar(self):
        pass
