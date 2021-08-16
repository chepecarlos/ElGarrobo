from libreria.FuncionesArchivos import ObtenerValor, SalvarValor
from libreria.acciones.EmularTeclado import ComandoEscribir

import MiLibrerias

logger = MiLibrerias.ConfigurarLogging(__name__)

def AccionDataArchivo(accion):
    """Acciones de Archivo."""
    accion = accion['data_archivo']
    Opcion = accion['opcion']
    if Opcion == "asignar":
        logger.info(f"Asignar Valor {accion['archivo']}[{accion['atributo']}] a {accion['valor']}")
        SalvarValor(accion['archivo'], accion['atributo'], accion['valor'])
    elif Opcion == "agregar":
        logger.info(f"Agregar Valor {accion['archivo']}[{accion['atributo']}] a {accion['valor']}")
        Valor = ObtenerValor(accion['archivo'], accion['atributo'])
        Valor += accion['valor']
        SalvarValor(accion['archivo'], accion['atributo'], Valor)
    elif Opcion == "minimo":
        Valor = ObtenerValor(accion['archivo'], accion['atributo'])
        if Valor < accion['valor']:
            Valor = accion['valor']
            SalvarValor(accion['archivo'], accion['atributo'], Valor)
            logger.info(f"Poner Minimo {accion['archivo']}[{accion['atributo']}] a {Valor}")
    elif Opcion == "maximo":
        Valor = ObtenerValor(accion['archivo'], accion['atributo'])
        Maximo = ObtenerValor(accion['archivo'], accion['valor'])
        if Valor > Maximo:
            Valor = Maximo
            SalvarValor(accion['archivo'], accion['atributo'], Valor)
            logger.info(f"Poner Maximo {accion['archivo']}[{accion['atributo']}] a {Valor}")
    elif Opcion == "pegar":
        Id = ObtenerValor(accion['archivo'], accion['atributo'])
        ComandoEscribir()
