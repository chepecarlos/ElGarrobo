from dataclasses import dataclass


@dataclass
class valoresAcciones:

    atributo: str
    valor: any

    def __str__(self) -> str:
        return f"{self.atributo} = {self.valor}"
