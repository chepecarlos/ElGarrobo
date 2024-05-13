"""Acciones de Sonido."""

# https://github.com/jiaaro/pydub
import multiprocessing

from pydub import AudioSegment
from pydub.playback import play

from elGarobo.miLibrerias import (ConfigurarLogging, ObtenerFolderConfig, UnirPath)

logger = ConfigurarLogging(__name__)

listaSonidos = []


def AccionSonido(accionActual, folder):
    """Acciones de Sonido."""
    if accionActual.get("sonido") == "parar":
        PararReproducion()
    else:
        Reproducir(accionActual, folder)


def Sonido(Archivo, Ganancia):
    """Reproducir sonido."""
    try:
        if Archivo.endswith(".wav"):
            sound = AudioSegment.from_file(Archivo, format="wav")
        elif Archivo.endswith(".mp3"):
            sound = AudioSegment.from_file(Archivo, format="mp3")
        else:
            logger.warning(f"Formato no soportado {Archivo}")
            return
        logger.info(f"Reproducir[{Archivo}]")
        play(sound + Ganancia)
        logger.info(f"Termino[{Archivo}]")
    except FileNotFoundError:
        logger.warning(f"No se encontro {Archivo}")


def Reproducir(opciones):
    """
    Crear un susproceso para Reproduccion.

    sonido -> stl
        direcion del sonido
    ganancia -> float
        ganancia en decibeles, a aumentar o bajar el sonido
    folder -> stl
        direcion del folder del sonido
    """
    global listaSonidos
    archivo = opciones.get("sonido")

    if archivo is not None:
        ganancia = opciones.get("ganancia", 0)
        folder = opciones.get("folder", ObtenerFolderConfig()) 
        ganancia = opciones.get("ganancia", 0)
        archivo = UnirPath(folder, archivo)

        procesoSonido = multiprocessing.Process(target=Sonido, args=(archivo, ganancia))
        procesoSonido.start()
        listaSonidos.append(procesoSonido)


def PararReproducion(opciones):
    """
    Parar todos los susprocesos de repoduccion de sonido.
    """
    global listaSonidos
    logger.info(f"Parar Sonidos [{len(listaSonidos)}]")
    for Sonido in listaSonidos:
        Sonido.terminate()
    listaSonidos = []
