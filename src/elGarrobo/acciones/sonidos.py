"""Acciones de Sonido."""

# https://github.com/jiaaro/pydub
# https://stackoverflow.com/questions/47596007/stop-the-audio-from-playing-in-pydub
# import multiprocessing
from multiprocessing import Process

from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerFolderConfig, UnirPath

logger = ConfigurarLogging(__name__)

listaSonidos = []


def AccionSonido(accionActual, folder):
    """Acciones de Sonido."""
    if accionActual.get("sonido") == "parar":
        PararReproducion()
    else:
        Reproducir(accionActual, folder)


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
        archivo = UnirPath(folder, archivo)

        try:
            if archivo.endswith(".wav"):
                sound = AudioSegment.from_file(archivo, format="wav")
            elif archivo.endswith(".mp3"):
                sound = AudioSegment.from_file(archivo, format="mp3")
            else:
                logger.warning(f"Formato no soportado {archivo}")
                return
            logger.info(f"Reproducir[{archivo}]")
            playback = _play_with_simpleaudio(sound + ganancia)
            listaSonidos.append(playback)
            logger.info(f"Termino[{archivo}]")
        except FileNotFoundError:
            logger.warning(f"No se encontro {archivo}")


def PararReproducion(opciones):
    """
    Parar todos los subprocess de reproducción de sonido.
    """
    global listaSonidos
    logger.info(f"Parar Sonidos [{len(listaSonidos)}]")
    for Sonido in listaSonidos:
        Sonido.stop()
    listaSonidos = []
