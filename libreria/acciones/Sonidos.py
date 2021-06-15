"""Modulo para acciones de produccion de sonido."""

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
        Reproducir(AccionActual)


def Sonido(Archivo, Ganancia):
    """Reproducir sonido."""
    try:
        if Archivo.endswith(".wav"):
            sound = AudioSegment.from_file(Archivo, format="wav")
        elif Archivo.endswith(".mp3"):
            sound = AudioSegment.from_file(Archivo, format="mp3")
        logger.info(f"Empezar a repoducir {Archivo}")
        play(sound + Ganancia)
        logger.info(f"Terminando de repoducir {Archivo}")
    except FileNotFoundError:
        logger.warning(f"No se encontro {Archivo}")


def Reproducir(AccionActual):
    """Crear un susproceso para Reproduccion."""
    global ListaSonidos
    Archivo = AccionActual['sonido']
    Ganancia = 0
    if 'ganancia' in AccionActual:
        Ganancia = AccionActual['ganancia']
    # TODO recorde del audio
    logger.info(f"Repoduciendo {Archivo}")
    Archivo = UnirPath(ObtenerConfig(), Archivo)
    PSonido = multiprocessing.Process(target=Sonido, args=[Archivo, Ganancia])
    PSonido.start()
    ListaSonidos.append(PSonido)


def PararReproducion():
    """Parar susprocesos de repoduccion de sonido."""
    global ListaSonidos
    logger.info("Parar Reproducion de Sonidos")
    for Sonido in ListaSonidos:
        Sonido.terminate()
