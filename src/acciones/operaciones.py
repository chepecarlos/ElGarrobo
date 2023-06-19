"""Acciones de Operaciones."""

from MiLibrerias import ConfigurarLogging, FuncionesArchivos

logger = ConfigurarLogging(__name__)


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
    numero = opciones.get("numero", 0)
    minimo = opciones.get("minomo", 0)
    maximo = opciones.get("maximo", 0)

    return constrain(numero, minimo, maximo)


def operacionConcatenar(opciones):
    texto = ""
    if type(opciones) is dict:
        opciones = sorted(opciones.items(), key=lambda x: x[0])
        for mensaje in opciones:
            texto += mensaje[1]
    logger.info(f"Concatenar[{texto}]")
    return texto


def operacionAsignar(opciones):
    # TODO: todo los valore sde opciones a cajon
    return opciones.get("valor")
