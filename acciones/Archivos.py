from MiLibrerias import ObtenerValor, SalvarValor

from MiLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


def LeerValor(Opciones):
    Archivo = None
    Atributo = None
    if 'archivo' in Opciones:
        Archivo = Opciones['archivo']
    if 'atributo' in Opciones:
        Atributo = Opciones['atributo']
    Logger.info(f"Leer[{Atributo}]:{Archivo}")
    return ObtenerValor(Archivo, Atributo)

def EscrivirValor(Opciones):
    Archivo = None
    Atributo = None
    Valor = None
    if 'archivo' in Opciones:
        Archivo = Opciones['archivo']
    if 'atributo' in Opciones:
        Atributo = Opciones['atributo']
    if 'valor' in Opciones:
        Valor = Opciones['valor']
    SalvarValor(Archivo, Atributo, Valor)
    pass

