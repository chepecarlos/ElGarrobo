class valoresAcciones:
    def __init__(self, atributo, valor) -> None:
        self.atributo = atributo
        self.valor = valor

    def __str__(self) -> str:
        return f"{self.atributo} = {self.valor}"
