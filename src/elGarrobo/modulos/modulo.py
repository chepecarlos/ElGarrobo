from elGarrobo.accionesOOP.heramientas.valoresAccion import valoresAcciones


class modulo:

    nombre: str

    def obtenerValor(self, listaValores: list[valoresAcciones], atributo: str):
        """Devuelve el valores configurado"""
        for valor in listaValores:
            if atributo == valor.atributo:
                return valor.valor
