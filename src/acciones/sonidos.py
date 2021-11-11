"""Modulo para acciones de produccion de sonido."""

# https://github.com/jiaaro/pydub
import multiprocessing

from pydub import AudioSegment
from pydub.playback import play

from MiLibrerias import ConfigurarLogging
from MiLibrerias import ObtenerFolderConfig, UnirPath, RelativoAbsoluto

logger = ConfigurarLogging(__name__)

ListaSonidos = []


def AccionSonido(AccionActual, Folder):
    """Acciones de Sonido."""
    if AccionActual["sonido"] == "parar":
        PararReproducion()
    else:
        Reproducir(AccionActual, Folder)


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
    global ListaSonidos
    if "sonido" in opciones:
        Archivo = opciones["sonido"]

        Ganancia = 0
        if "ganancia" in opciones:
            Ganancia = opciones["ganancia"]

        if "folder" in opciones:
            Folder = opciones["folder"]
        else:
            Folder = ObtenerFolderConfig()
        # TODO recorde del audio
        # Archivo = RelativoAbsoluto(Archivo, Folder)
        Archivo = UnirPath(Folder, Archivo)

        PSonido = multiprocessing.Process(target=Sonido, args=[Archivo, Ganancia])
        PSonido.start()
        ListaSonidos.append(PSonido)


def PararReproducion(opciones):
    """
    Parar todos los susprocesos de repoduccion de sonido.
    """
    global ListaSonidos
    logger.info(f"Parar Sonidos [{len(ListaSonidos)}]")
    for Sonido in ListaSonidos:
        Sonido.terminate()
    ListaSonidos = []
