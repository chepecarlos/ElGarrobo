"""Acciones de archivos."""

from MiLibrerias import ConfigurarLogging, FuncionesArchivos

logger = ConfigurarLogging(__name__)


def leerValor(opciones):
    """
    Lee un atributo de un archivo y lo devuelve

    archivo -> stl
        Nombre del archivo
    atributo -> stl
        Nombre del atributo
    """
    archivo = None
    atributo = None
    if "archivo" in opciones:
        archivo = opciones["archivo"]
    if "atributo" in opciones:
        atributo = opciones["atributo"]
    if archivo is None:
        logger.info(f"Requerido[archivo,]")
        return

    data = None
    if atributo is None:
        logger.info(f"Leer[{archivo}]")
        data = FuncionesArchivos.ObtenerArchivo(archivo)
    else:
        logger.info(f"Leer[{archivo}]: {atributo}")
        data = FuncionesArchivos.ObtenerValor(archivo, atributo)
    logger.info(f"Leido[{data}]")
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
    archivo = None
    atributo = None
    valores = None
    local = True
    if "archivo" in opciones:
        archivo = opciones["archivo"]
    if "valores" in opciones:
        valores = opciones["valores"]
    if "local" in opciones:
        local = opciones["local"]

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
    archivo = None
    atributo = None
    valor = None
    local = True
    if "archivo" in opciones:
        archivo = opciones["archivo"]
    if "atributo" in opciones:
        atributo = opciones["atributo"]
    if "valor" in opciones:
        valor = opciones["valor"]
    if "local" in opciones:
        local = opciones["local"]

    if archivo is None or valor is None:
        logger.info("Falta informacion para")
        return

    if atributo is None:
        logger.info(f"Escribir[{archivo}]={valor}")
        FuncionesArchivos.SalvarArchivo(archivo, valor)
        # TODO: Salvar en No local
    else:
        logger.info(f"Escribir[{archivo}] {atributo}={valor}")
        FuncionesArchivos.SalvarValor(archivo, atributo, valor, local=local)
