import logging
from MiLibrerias import ObtenerValor, SalvarValor
from MiLibrerias import ObtenerArchivo, SalvarArchivo
from MiLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


def LeerValor(Opciones):
    """
    Lee un Atributo de un Archivo y lo devuelve

    archivo -> stl
        Nombre del archivo
    atributo -> stl
        Nombre del atributo
    """
    Archivo = None
    Atributo = None
    if "archivo" in Opciones:
        Archivo = Opciones["archivo"]
    if "atributo" in Opciones:
        Atributo = Opciones["atributo"]
    if Archivo is None:
        Logger.info(f"Requerido[Archivo,]")
        return

    Data = None
    if Atributo is None:
        Logger.info(f"Leer[{Archivo}]")
        Data = ObtenerArchivo()
    else:
        Logger.info(f"Leer[{Archivo}]: {Atributo}")
        Data = ObtenerValor(Archivo, Atributo)
    return Data


def EscrivirValor(Opciones):
    """
    Escribe un Atributo de un Archivo

    archivo -> stl
        Nombre del archivo
    atributo -> stl
        Nombre del atributo
    valor -> everything
    """
    Archivo = None
    Atributo = None
    Valor = None
    Local = True
    if "archivo" in Opciones:
        Archivo = Opciones["archivo"]
    if "atributo" in Opciones:
        Atributo = Opciones["atributo"]
    if "valor" in Opciones:
        Valor = Opciones["valor"]
    if "local" is Opciones:
        Local = Opciones["local"]

    if Archivo is None or Valor is None:
        Logger.info("Falta informacion para")

    if Atributo is None:
        Logger.info(f"Escribir[{Archivo}]={Valor}")
        SalvarArchivo(Archivo, Valor)
        # TODO: Salvar en No local
    else:
        Logger.info(f"Escribir[{Archivo}] {Atributo}={Valor}")
        SalvarValor(Archivo, Atributo, Valor, Local=Local)
