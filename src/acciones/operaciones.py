"""Acciones de Operaciones."""


def constrain(n, minn, maxn):
    return max(min(maxn, n), minn)


def OperacionConstrain(opciones):
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
    if "numero" in opciones:
        Numero = opciones["numero"]
    if "minimo" in opciones:
        Minimo = opciones["minimo"]
    if "maximo" in opciones:
        Maximo = opciones["maximo"]

    return constrain(Numero, Minimo, Maximo)
