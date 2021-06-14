import logging
import os
from pathlib import Path
from datetime import datetime

NivelLog = logging.DEBUG

def NivelLogging(Nivel):
    # TODO aun no funciona niveles de log
    global NivelLog
    NivelLog = Nivel


def ConfigurarLogging(logger):
    global NivelLog
    logger.setLevel(NivelLog)

    ArchivoLog = '.config/elgatoalsw'
    ArchivoLog = ArchivoConfiguracion = os.path.join(Path.home(), ArchivoLog)
    ArchivoLog = os.path.join(ArchivoLog, 'logs')

    if not os.path.isdir(ArchivoLog):
        os.makedirs(ArchivoLog)

    ArchivoLog = ArchivoLog + '/{:%Y-%m-%d %H:%M:%S}.log'.format(datetime.now())

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(ArchivoLog)
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
