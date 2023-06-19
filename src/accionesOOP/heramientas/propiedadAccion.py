from .valoresAccion import valoresAcciones

class propiedadAccion:
    """
    clase de las propiedad de una accion
    """

    def __init__(self, lista=None) -> None:
        if isinstance(lista, dict):
            self.nombre = lista["nombre"]
            self.atributo = lista["atributo"]
            self.tipo = lista["tipo"]
            self.obligatorio = lista["obligatorio"]
            self.descripcion = lista["descripcion"]
            self.ejemplo = None
            if "ejemplo" in lista:
                self.ejemplo = lista["ejemplo"]

    def mismoTipo(self, valor) -> bool:
        return type(valor) == self.tipo

    def mismoAtributo(self, atributo) -> bool:
        if isinstance(atributo, valoresAcciones):
            return atributo.atributo == self.atributo
        return atributo == self.atributo

    def __str__(self) -> str:
        obligatorio = ""
        if self.obligatorio:
            obligatorio = "*"
        return f"Propiedad: {self.nombre}'{self.atributo}'[{self.tipo.__name__}]{obligatorio}"
