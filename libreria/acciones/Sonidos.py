# https://github.com/jiaaro/pydub

from pydub import AudioSegment
from pydub.playback import play

import multiprocessing
import logging
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import UnirPath, ObtenerConfig

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)

ListaSonidos = []


def AccionSonido(AccionActual):
    """Acciones de Sonido."""
    if AccionActual['sonido'] == 'parar':
        PararReproducion()
    else:
        Reproducir(AccionActual['sonido'])


def Sonido(Archivo):
    """Reproducir sonido."""
    try:
        if Archivo.endswith(".wav"):
            sound = AudioSegment.from_file(Archivo, format="wav")
        elif Archivo.endswith(".mp3"):
            sound = AudioSegment.from_file(Archivo, format="mp3")
        logger.info(f"Empezar a repoducir {Archivo}")
        play(sound)
        logger.info(f"Terminando de repoducir {Archivo}")
    except FileNotFoundError:
        logger.warning(f"No se encontro {Archivo}")


def Reproducir(Archivo):
    """Crear un susproceso para Reproduccion."""
    global ListaSonidos
    logger.info(f"Repoduciendo {Archivo}")
    Archivo = UnirPath(ObtenerConfig(), Archivo)
    PSonido = multiprocessing.Process(target=Sonido, args=[Archivo])
    PSonido.start()
    ListaSonidos.append(PSonido)


def PararReproducion():
    """Parar susprocesos de repoduccion de sonido."""
    global ListaSonidos
    logger.info("Parar Reproducion de Sonidos")
    for Sonido in ListaSonidos:
        Sonido.terminate()
