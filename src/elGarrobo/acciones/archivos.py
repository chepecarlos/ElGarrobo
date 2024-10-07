"""Acciones de archivos."""

from elGarrobo.miLibrerias import ConfigurarLogging, FuncionesArchivos

logger = ConfigurarLogging(__name__)


def leerValor(opciones):
    """
    Lee un atributo de un archivo y lo devuelve

    archivo -> stl
        Nombre del archivo
    atributo -> stl
        Nombre del atributo
    """
    archivo = opciones.get("archivo")
    atributo = opciones.get("atributo")
    if archivo is None:
        logger.info("Requerido[archivo,]")
        return

    data = None
    if atributo is None:
        logger.info(f"Leer[{archivo}]")
        data = FuncionesArchivos.ObtenerArchivo(archivo)
    else:
        logger.info(f"Leer[{archivo}]: {atributo}")
        data = FuncionesArchivos.ObtenerValor(archivo, atributo)
    logger.info(f"Leído[{data}]")
    return data


def escribirValores(opciones):
    """
    Escribe un atributo de un archivo

    archivo -> stl
        Nombre del archivo
    atributo -> stl
        Nombre del atributo
    valor -> everything
    """
    archivo = opciones.get("archivo")
    valores = opciones.get("valores")
    atributo = opciones.get("atributo")
    local = opciones.get("local", True)

    if archivo is None or valores is None:
        logger.info("Falta información para")
        return

    for atributo in valores:
        logger.info(f"Escribir[{archivo}] {atributo}={valores.get(atributo)}")
        FuncionesArchivos.SalvarValor(archivo, atributo, valores.get(atributo), local=local)


def escribirValor(opciones):
    """
    Escribe un atributo de un archivo

    archivo -> stl
        Nombre del archivo
    atributo -> stl
        Nombre del atributo
    valor -> everything
    """
    archivo = opciones.get("archivo")
    atributo = opciones.get("atributo")
    valor = opciones.get("valor")
    local = opciones.get("local", True)

    if archivo is None or valor is None:
        logger.info("Falta información para")
        return

    if atributo is None:
        logger.info(f"Escribir[{archivo}]={valor}")
        FuncionesArchivos.SalvarArchivo(archivo, valor)
        # TODO: Salvar en No local
    else:
        logger.info(f"Escribir[{archivo}] {atributo}={valor}")
        FuncionesArchivos.SalvarValor(archivo, atributo, valor, local=local)


def escribirArchivo(opciones):

    archivo = opciones.get("archivo")
    data = opciones.get("data")

    if archivo is None or data is None:
        logger.info("Falta información para")
        return

    print(archivo)
    print(data)

    FuncionesArchivos.SalvarArchivo(archivo, data)
