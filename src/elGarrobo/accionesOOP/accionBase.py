from .heramientas.propiedadAccion import propiedadAccion
from .heramientas.valoresAccion import valoresAcciones


class accionBase:
    """
    clase base de las acciones del sistema.
    """

    funcion: callable = None
    funcionExterna: callable = None

    def __init__(self, nombre: str, comando: str, descripcion: str) -> None:
        self.nombre = nombre
        self.comando = comando
        self.descripcion = descripcion
        self.listaPropiedades: list[propiedadAccion] = []
        self.listaValores: list[valoresAcciones] = list()
        self.gui = True
        self.error = False

    def agregarPropiedad(self, lista: dict = None) -> None:
        """Agrega propiedad a la accion"""
        nuevaPropiedad = propiedadAccion(lista)
        self.listaPropiedades.append(nuevaPropiedad)

    def configurar(self, lista: dict = None) -> None:
        """Recive la lista propiedades para ejecutar"""

        self.listaValores = []
        if lista is None:
            return

        if isinstance(lista, dict):
            for atributo in lista:
                valor = lista[atributo]
                if self.confirmarPropiedad(atributo, valor):
                    valorActual = valoresAcciones(atributo, valor)
                    self.listaValores.append(valorActual)
                else:
                    print(f"AcciónPOO[Error] Atribulo {atributo} incorrecto {type(valor)}")
                    self.error = True

    def ejecutar(self) -> bool:
        """Ejecuta la accion si es posible"""
        if not self.sePuedeEjecutar():
            print("AcciónPOO[Error] - Falta Propiedades.")
            return False

        if callable(self.funcion):
            self.funcion()
            return True

        if callable(self.funcionExterna):
            self.funcionExterna(self.listaValores)
            return True

        print("AcciónPOO[Error] - Falta Función.")
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
                    return False
        return True

    def confirmarPropiedad(self, atributo, valor) -> bool:
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

    def __str__(self) -> str:
        return f"Accion: {self.nombre}[{self.atributo}]"
