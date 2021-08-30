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
    if AccionActual['sonido'] == 'parar':
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
        logger.info(f"Empezar a repoducir {Archivo}")
        play(sound + Ganancia)
        logger.info(f"Terminando de repoducir {Archivo}")
    except FileNotFoundError:
        logger.warning(f"No se encontro {Archivo}")


# def Reproducir(AccionActual, Folder):
def Reproducir(opciones):
    """Crear un susproceso para Reproduccion."""
    global ListaSonidos
    if 'sonido' in opciones:
        Archivo = opciones['sonido']

        Ganancia = 0
        if 'ganancia' in opciones:
            Ganancia = opciones['ganancia']

        if 'folder' in opciones:
            Folder = opciones['folder']
        # TODO recorde del audio
        logger.info(f"Repoduciendo {Archivo}")
        Archivo = RelativoAbsoluto(Archivo, Folder)
        Archivo = UnirPath(ObtenerFolderConfig(), Archivo)
        
        PSonido = multiprocessing.Process(target=Sonido, args=[Archivo, Ganancia])
        PSonido.start()
        ListaSonidos.append(PSonido)


def PararReproducion(opciones):
    """Parar susprocesos de repoduccion de sonido."""
    global ListaSonidos
    logger.info(f"Parar Reproducion de Sonidos {len(ListaSonidos)}")
    for Sonido in ListaSonidos:
        Sonido.terminate()
    ListaSonidos = []
