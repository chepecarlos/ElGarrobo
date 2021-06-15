# https://simpleaudio.readthedocs.io/en/latest/installation.html#installation-ref

import multiprocessing
import logging
import simpleaudio as sa
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import UnirPath, ObtenerConfig

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)

ListaSonidos = []


def AccionSonido(AccionActual):
    if AccionActual['sonido'] == 'parar':
        PararReproducion()
    else:
        Reproducir(AccionActual['sonido'])


def Sonido(Archivo):
    try:
        sound = sa.WaveObject.from_wave_file(Archivo)
        Repoductor = sound.play()
        logger.info(f"Empezar a repoducir {Archivo}")
        Repoductor.wait_done()
        logger.info(f"Terminando de repoducir {Archivo}")
    except FileNotFoundError:
        logger.warning(f"No se encontro {Archivo}")


def Reproducir(Archivo):
    global ListaSonidos
    logger.info(f"Repoduciendo {Archivo}")
    Archivo = UnirPath(ObtenerConfig(), Archivo)
    PSonido = multiprocessing.Process(target=Sonido, args=[Archivo])
    PSonido.start()
    ListaSonidos.append(PSonido)


def PararReproducion():
    global ListaSonidos
    logger.info("Parar Reproducion de Sonidos")
    for Sonido in ListaSonidos:
        Sonido.terminate()
