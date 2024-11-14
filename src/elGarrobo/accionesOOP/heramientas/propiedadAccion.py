from .valoresAccion import valoresAcciones


class propiedadAccion:
    """
    clase de las propiedad de una accion
    """

    def __init__(self, lista: dict = None) -> None:
        if isinstance(lista, dict):
            self.nombre: str = lista["nombre"]
            self.atributo: str = lista["atributo"]
            self.tipo = lista["tipo"]
            self.obligatorio = lista["obligatorio"]
            self.descripcion = lista["descripcion"]
            self.ejemplo = lista.get("ejemplo")
            self.defecto = lista.get("defecto")

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
