from MiLibrerias import ObtenerValor, SalvarValor

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
    if 'archivo' in Opciones:
        Archivo = Opciones['archivo']
    if 'atributo' in Opciones:
        Atributo = Opciones['atributo']
    Logger.info(f"Leer[{Archivo}]: {Atributo}")
    return ObtenerValor(Archivo, Atributo)


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
    if 'archivo' in Opciones:
        Archivo = Opciones['archivo']
    if 'atributo' in Opciones:
        Atributo = Opciones['atributo']
    if 'valor' in Opciones:
        Valor = Opciones['valor']
    
    Logger.info(f"Escribir[{Archivo}] {Atributo}={Valor}")
    SalvarValor(Archivo, Atributo, Valor)
