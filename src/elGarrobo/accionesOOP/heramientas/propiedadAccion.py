from __future__ import annotations

from .valoresAccion import valoresAcciones


class propiedadAccion:
    """
    clase de las propiedad de una acción de los atributos que se necesitan
    """

    nombre: str
    atributo: str
    tipo: list | str
    obligatorio: bool
    descripcion: str
    ejemplo: str
    defecto: any

    def __init__(self, lista: dict = None) -> None:
        if isinstance(lista, dict):
            self.nombre: str = lista.get("nombre")
            self.atributo: str = lista.get("atributo")
            self.tipo: list | str = lista.get("tipo")
            self.obligatorio: bool = lista.get("obligatorio", False)
            self.descripcion: str = lista.get("descripcion")
            self.ejemplo: str = lista.get("ejemplo")
            self.defecto: any = lista.get("defecto")

    def mismoTipo(self, valor: any) -> bool:
        if isinstance(self.tipo, list):
            for tipoActual in self.tipo:
                if type(valor) == tipoActual:
                    return True
        return type(valor) == self.tipo

    def mismoAtributo(self, atributo) -> bool:
        if isinstance(atributo, valoresAcciones):
            return atributo.atributo == self.atributo
        return atributo == self.atributo

    def __eq__(self, propiedad: propiedadAccion):
        if isinstance(propiedad, valoresAcciones):
            return propiedad.atributo == self.atributo
        return self.atributo == propiedad.atributo

    def __str__(self) -> str:
        obligatorio: str = ""
        if self.obligatorio:
            obligatorio = "*"
        return f"Propiedad: {self.nombre}'{self.atributo}'[{self.tipo}]{obligatorio}"
