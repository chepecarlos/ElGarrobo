class dispositivoSonido(object):
    "Información de dispositivo de sonido"

    nombre = None
    "nombre del dispositivo"
    volumen: list[int] = [0, 0]
    "volumen en diferentes canales"
    mute = None
    "esta silenciado el dispositivo"

    def __str__(self) -> str:
        if self.mute:
            return f"{self.nombre}-{self.mute}"
        else:
            return f"{self.nombre} {self.volumen}"
