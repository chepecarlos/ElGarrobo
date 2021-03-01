import logging
import os
from pathlib import Path
from datetime import datetime

ArchivoLog = ArchivoConfiguracion = os.path.join(Path.home(), '.config/elgatoalsw')
ArchivoLog = ArchivoLog + '/logs/{:%Y-%m-%d %H:%M:%S}.log'.format(datetime.now())

NivelLog = logging.DEBUG


def NivelLogging(Nivel):
    # TODO aun no funciona
    global NivelLog
    NivelLog = Nivel
    pass


def ConfigurarLogging(logger):
    global ArchivoLog
    global NivelLog
    logger.setLevel(NivelLog)
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(ArchivoLog)
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
