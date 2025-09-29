from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

"""Acción para esperar un tiempo"""

from elGarrobo.accionesOOP.accionBase import accionBase
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)

listaSonidos = []


class miReproductor:

    def __init__(self, data: np.ndarray, samplerate: int, logger=None):
        self.log = logger
        self.data = np.asarray(data, dtype=np.float32, order="C")
        self.samplerate = int(samplerate)
        self.channels = self.data.shape[1] if self.data.ndim > 1 else 1
        self._pos = 0
        self._stopping = False

        self.stream = sd.OutputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="float32",
            callback=self._callback,
        )

    def _callback(self, outdata, frames, time, status):
        if status and self.log:
            self.log.warning(f"sounddevice status: {status}")

        if self._stopping:
            outdata.fill(0)
            raise sd.CallbackStop()

        end = self._pos + frames
        chunk = self.data[self._pos : end]

        n = len(chunk) if self.data.ndim == 1 else chunk.shape[0]
        if n == 0:
            outdata.fill(0)
            raise sd.CallbackStop()

        if self.channels == 1:
            outdata[:n, 0] = chunk
        else:
            outdata[:n, :] = chunk

        if n < frames:
            outdata[n:, :].fill(0)
            raise sd.CallbackStop()

        self._pos = end

    def start(self):
        self.stream.start()
        return self

    def stop(self):
        self._stopping = True
        try:
            self.stream.abort()
        except Exception:
            pass
        try:
            self.stream.close()
        except Exception:
            pass

    def is_playing(self):
        return bool(self.stream.active)


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
            logger.warning(f"{self.nombre} No existe {rutaArchivo}")
            return

        try:
            # ¡Clave!: usa float32 para evitar el mismatch
            data, sr = sf.read(rutaArchivo, dtype="float32", always_2d=False)

            # Ganancia en dB (limita a [-1, 1] para evitar clipping)
            if ganancia:
                factor = 10 ** (ganancia / 20.0)
                data = np.clip(data * factor, -1.0, 1.0).astype("float32", copy=False)

            player = miReproductor(data, sr, logger=logger).start()
            listaSonidos.append(player)
            logger.info(f"Reproduciendo [{rutaArchivo}] (no bloqueante)")
        except Exception as e:
            logger.error(f"Error al reproducir {rutaArchivo}: {e}")


class accionPararReproducirones(accionBase):
    """Para todas las reproducciones un sonido"""

    nombre = "Parar Sonidos"
    comando = "detener_reproducion"
    descripcion = "Pata todas las reproducciones de sonidos"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.funcion = self.pararReproducion

    def pararReproducion(self):
        """
        Parar todos los subprocess de reproducción de sonido.
        """
        global listaSonidos
        logger.info(f"Parar Sonidos [{len(listaSonidos)}]")
        for p in listaSonidos:
            try:
                p.stop()
            except Exception as e:
                logger.warning(f"Error al detener stream: {e}")
        listaSonidos = []


if __name__ == "__main__":

    archivo = "/sonidos/golpe.wav"
    print("Empesando a Reproducir")

    accionTest: accionReproducir = accionReproducir()
    opciones = {"archivo": archivo}
    accionTest.configurar(opciones)
    accionTest.ejecutar()
    print("Reproduciendo")

    while _ := input("Press <Enter> to exit\n"):
        print("Iniciando: ----")
    print("Saliendo")
