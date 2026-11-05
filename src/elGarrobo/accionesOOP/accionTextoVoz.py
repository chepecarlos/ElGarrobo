"""Acción de texto a voz"""

import time
from pathlib import Path

import numpy as np

# https://github.com/OHF-Voice/piper1-gpl
from piper import PiperVoice, SynthesisConfig
from piper.download_voices import download_voice

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion
from .accionSonidos import reproducirAudio

Logger = ConfigurarLogging(__name__)

# Fuera del folder de config para no subir modelos de ~60 MB a los dotfiles
folderVoces = Path.home() / ".local/share/elgarrobo/voces"


class accionTextoVoz(accion):
    """Transforma texto a voz con Piper (sin internet)"""

    nombre = "Texto a voz"
    comando = "textovoz"
    categoria = "Sonido"
    descripcion = "Lee un texto en voz alta con Piper, sin internet; la primera vez baja la voz"

    voces: dict[str, PiperVoice] = {}
    "Voces ya cargadas, cargar un modelo tarda ~1 s"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadMensaje = propiedadAccion(
            nombre="Mensaje",
            tipo=str,
            obligatorio=True,
            atributo="mensaje",
            descripcion="texto a leer en voz alta",
            ejemplo="Hola Mundo",
        )

        propiedadVoz = propiedadAccion(
            nombre="Voz",
            tipo=str,
            obligatorio=False,
            atributo="voz",
            descripcion="voz de Piper (https://huggingface.co/rhasspy/piper-voices), se baja la primera vez",
            ejemplo="es_MX-claude-high",
            defecto="es_ES-davefx-medium",
        )

        propiedadVolumen = propiedadAccion(
            nombre="Volumen",
            tipo=[int, float],
            obligatorio=False,
            atributo="volumen",
            descripcion="volumen de la voz, 1 es normal",
            ejemplo="0.8",
            defecto=1,
        )

        propiedadVelocidad = propiedadAccion(
            nombre="Velocidad",
            tipo=[int, float],
            obligatorio=False,
            atributo="velocidad",
            descripcion="1 es normal, 1.5 más rápido, 0.8 más lento",
            ejemplo="1.2",
            defecto=1,
        )

        propiedadEsperar = propiedadAccion(
            nombre="Esperar",
            tipo=bool,
            obligatorio=False,
            atributo="esperar",
            descripcion="espera a que termine de hablar antes de seguir",
            ejemplo="true",
            defecto=True,
        )

        self.agregarPropiedad(propiedadMensaje)
        self.agregarPropiedad(propiedadVoz)
        self.agregarPropiedad(propiedadVolumen)
        self.agregarPropiedad(propiedadVelocidad)
        self.agregarPropiedad(propiedadEsperar)

        self.funcion = self.hablar

    def cargarVoz(self, nombre: str) -> PiperVoice:
        """Carga la voz, bajándola si no existe"""
        if nombre not in self.voces:
            folderVoces.mkdir(parents=True, exist_ok=True)
            download_voice(nombre, folderVoces)
            self.voces[nombre] = PiperVoice.load(str(folderVoces / f"{nombre}.onnx"))
        return self.voces[nombre]

    def hablar(self):
        """Lee el mensaje en voz alta"""
        mensaje = self.obtenerValor("mensaje")
        nombreVoz = self.obtenerValor("voz")

        try:
            voz = self.cargarVoz(nombreVoz)
        except Exception as error:
            Logger.error(f"TextoVoz[Error] no se pudo cargar la voz {nombreVoz}: {error}")
            return

        configuracion = SynthesisConfig(
            volume=self.obtenerValor("volumen"),
            length_scale=1 / self.obtenerValor("velocidad"),
        )
        audio = np.concatenate([parte.audio_float_array for parte in voz.synthesize(mensaje, configuracion)])

        Logger.info(f"TextoVoz[{mensaje}]")
        reproductor = reproducirAudio(audio, voz.config.sample_rate, f"TextoVoz {mensaje}")
        if self.obtenerValor("esperar"):
            while reproductor.is_playing():
                time.sleep(0.1)
