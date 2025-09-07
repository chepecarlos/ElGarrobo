from multiprocessing import Process
from pathlib import Path

from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio

"""Acción para esperar un tiempo"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)

listaSonidos = []


class accionReproducir(accionBase):
    """Reproduce un sonido"""

    nombre = "Reproducir Sonido"
    comando = "reproducion"
    descripcion = "Reproduce un sonido"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadArchivo = {
            "nombre": "Archivo",
            "tipo": str,
            "obligatorio": True,
            "atributo": "archivo",
            "descripcion": "pista a reproducira",
            "ejemplo": "sonido.mp4",
        }

        propiedadGanancia = {
            "nombre": "Ganancia",
            "tipo": int,
            "obligatorio": False,
            "atributo": "ganancia",
            "descripcion": "Cuanto se tiene que incrementar o bajar el volumen",
            "ejemplo": "5",
            "defecto": 0,
        }

        propiedadFolder = {
            "nombre": "Folder",
            "tipo": str,
            "obligatorio": False,
            "atributo": "folder",
            "descripcion": "Si en ruta absoluta, decir donde esta el pista de audio",
            "ejemplo": "/home/chepecarlos/sonidos",
        }

        self.agregarPropiedad(propiedadArchivo)
        self.agregarPropiedad(propiedadGanancia)
        self.agregarPropiedad(propiedadFolder)

        self.funcion = self.reproducir

    def reproducir(self):
        """
        Crear un susproceso para Reproduccion.
        """
        global listaSonidos

        archivo = self.obtenerValor("archivo")
        ganancia = self.obtenerValor("ganancia")
        folder = self.obtenerValor("folder")

        rutaArchivo = self.calcularRuta(archivo)

        if not Path(rutaArchivo).exists():
            Logger.warning(f"{self.nombre} No existe {rutaArchivo}")

        try:
            if rutaArchivo.endswith(".wav"):
                sound = AudioSegment.from_file(rutaArchivo, format="wav")
            elif rutaArchivo.endswith(".mp3"):
                rutaArchivo = AudioSegment.from_file(rutaArchivo, format="mp3")
            else:
                Logger.warning(f"Formato no soportado {rutaArchivo}")
                return
            Logger.info(f"Reproducir[{archivo}]")
            playback = _play_with_simpleaudio(sound + ganancia)
            if listaSonidos is None:
                listaSonidos = list()
            listaSonidos.append(playback)
            Logger.info(f"Termino Reproducir[{archivo}]")
        except FileNotFoundError:
            Logger.warning(f"{self.nombre} No existe {archivo}")


class accionPararReproducirones(accionBase):
    """Para todas las reproducciones un sonido"""

    nombre = "Parar Sonidos"
    comando = "detener_reproducion"
    descripcion = "Pata todas las reproducciones de sonidos"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.funcion = self.pararReproducion

    def pararReproducion(opciones):
        """
        Parar todos los subprocess de reproducción de sonido.
        """
        global listaSonidos
        Logger.info(f"Parar Sonidos [{len(listaSonidos)}]")
        for Sonido in listaSonidos:
            Sonido.stop()
        listaSonidos = list()
