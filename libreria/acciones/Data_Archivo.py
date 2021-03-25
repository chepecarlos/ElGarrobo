import logging

from libreria.FuncionesArchivos import SalvarValor
from libreria.FuncionesLogging import ConfigurarLogging

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


def AccionDataArchivo(accion):
    print(accion)
    accion = accion['data_archivo']
    Opcion = accion['opcion']
    if Opcion == "asignar":
        logger.info(f"Asignar Valor {accion['valor']} a {accion['archivo']}")
        SalvarValor(accion['archivo'], accion['atributo'], accion['valor'])
