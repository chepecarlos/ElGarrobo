import logging
import os
from pathlib import Path
from datetime import datetime

ArchivoLog = ArchivoConfiguracion = os.path.join(Path.home(), '.config/elgatoalsw')
ArchivoLog = ArchivoLog + '/logs/{:%Y-%m-%d %H:%M:%S}.log'.format(datetime.now())


def ConfigurarLogging(logger):
    global ArchivoLog
    # if ArchivoLog == "":
    #     ArchivoLog = getFolderLocal() + '/logs/{:%Y-%m-%d %H:%M:%S}.log'.format(datetime.now())
    logger.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(ArchivoLog)
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
