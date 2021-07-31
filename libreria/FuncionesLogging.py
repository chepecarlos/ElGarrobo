import logging
import os
import sys
from pathlib import Path
from datetime import datetime


NivelLog = logging.DEBUG


def NivelLogging(Nivel):
    """Nivel de depuracion."""
    # TODO aun no funciona niveles de log
    global NivelLog
    NivelLog = Nivel


def ConfigurarLogging(logger):
    """Configura el archivo de depuracion."""
    global NivelLog
    logger.setLevel(NivelLog)

    Programa = os.path.basename(sys.argv[0]).lower()
    Programa = os.path.splitext(Programa)[0]

    ArchivoLog = os.path.join('.config', Programa)
    ArchivoLog = os.path.join(Path.home(), ArchivoLog)
    ArchivoLog = os.path.join(ArchivoLog, 'logs')

    if not os.path.isdir(ArchivoLog):
        os.makedirs(ArchivoLog)

    ArchivoLog = ArchivoLog + '/{:%Y-%m-%d_%H:%M:%S}.log'.format(datetime.now())

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(ArchivoLog)
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
