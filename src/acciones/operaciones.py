"""Acciones de Operaciones."""


def constrain(n, minn, maxn):
    return max(min(maxn, n), minn)


def OperacionConstrain(Opciones):
    """
    limita un numero para que no salga de un rando

    numero -> float
        numero a limitar
    minimo -> float
        rando inferior
    maximo -> float
        rando superior
    """
    Numero = 0
    Minimo = 0
    Maximo = 0
    if "numero" in Opciones:
        Numero = Opciones["numero"]
    if "minimo" in Opciones:
        Minimo = Opciones["minimo"]
    if "maximo" in Opciones:
        Maximo = Opciones["maximo"]

    return constrain(Numero, Minimo, Maximo)
