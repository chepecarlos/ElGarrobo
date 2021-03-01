import logging

from datetime import datetime

from libreria.FuncionesArchivos import getFolderLocal

ArchivoLog = ""


def ConfigurarLogging(logger):
    global ArchivoLog
    if ArchivoLog == "":
        ArchivoLog = getFolderLocal() + '/logs/{:%Y-%m-%d %H:%M:%S}.log'.format(datetime.now())
    logger.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(ArchivoLog)
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
