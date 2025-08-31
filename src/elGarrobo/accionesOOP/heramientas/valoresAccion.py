class valoresAcciones:
    atributo: str
    valor: any

    def __init__(self, atributo: str, valor: any) -> None:
        self.atributo: str = atributo
        self.valor: any = valor

    def __str__(self) -> str:
        return f"{self.atributo} = {self.valor}"
