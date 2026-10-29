"""Acción que no hace nada, para botones que solo muestran información"""

from .accion import accion


class accionNada(accion):
    """Acción que no hace nada, para botones que solo muestran información (ej. un titulo por MQTT)"""

    nombre = "Nada"
    comando = "nada"
    categoria = "ElGarrobo"
    descripcion = "No hace nada, útil para botones que solo muestran texto o estado"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)
        self.funcion = lambda: None
