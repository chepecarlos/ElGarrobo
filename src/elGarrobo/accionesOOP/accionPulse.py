import re
import subprocess as sp

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor, SalvarValor

from .accion import accion, propiedadAccion
from .accionOS import accionOS
from .dataclass.dispositivoSonido import dispositivoSonido

Logger = ConfigurarLogging(__name__)


class accionVolumen(accion):
    """Siguiente pagina en Dispositivo StreamDeck"""

    nombre = "Volumen"
    comando = "volumen"
    descripcion = "Cambia Volumen dispositivo virtual de pulse"

    archivoPulse = "data/pulse.md"
    "Ruta donde se guarda la información de PulseAudio"

    propiedadDispositivo: propiedadAccion = propiedadAccion(
        nombre="Dispositivo",
        tipo=str,
        obligatorio=True,
        atributo="dispositivo",
        descripcion="Nombre del dispositivo a cambiar volumen",
        ejemplo="microfono",
    )

    propiedadValor: propiedadAccion = propiedadAccion(
        nombre="Valor",
        tipo=int,
        obligatorio=True,
        atributo="valor",
        descripcion="Incremento o decremento de volumen",
        ejemplo="+5",
    )

    propiedadOpciones: propiedadAccion = propiedadAccion(
        nombre="Opción",
        tipo=str,
        obligatorio=False,
        atributo="opcion",
        descripcion="asignar o incrementar",
        ejemplo="+5",
        defecto="asignar",
    )

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.agregarPropiedad(self.propiedadDispositivo)
        self.agregarPropiedad(self.propiedadValor)
        self.agregarPropiedad(self.propiedadOpciones)

        self.funcion = self.cambiarVolumen

    def cambiarVolumen(self) -> None:

        dispositivo = self.obtenerValor("dispositivo")
        valor = self.obtenerValor("valor")
        opcion = self.obtenerValor("opcion")

        comando = None

        if dispositivo is None or valor is None:
            Logger.info("Faltan opciones")
            return

        if opcion == "asignar":
            comando = f"pactl set-sink-volume {dispositivo} {valor}%"
        elif opcion == "incremento":
            simbolo = "+" if valor > 0 else ""
            comando = f"pactl set-sink-volume {dispositivo} {simbolo}{valor}%"
        elif opcion == "balance":
            texto: str = ObtenerValor(self.archivoPulse, dispositivo)
            if texto is None:
                Logger.warning(f"Error con Disposition {dispositivo}")
                return

            nivel: str = self.obtenerPorcentajes(texto)
            if nivel is None:
                Logger.warning(f"Error con Nivel de Disposition {dispositivo}")
                return
            nivelIzquierda: int = 0
            nivelDerecha: int = 0
            if len(nivel) == 1:
                nivelMax = nivel[0]
            else:
                nivelMax = nivel[0] if nivel[0] > nivel[1] else nivel[1]
            nivelMax: int = int(nivelMax)
            if valor == 50:
                nivelIzquierda = nivelMax
                nivelDerecha = nivelMax
            if valor < 50:
                nivelIzquierda = nivelMax
                fuerza: float = 1 - (50 - valor) / 50
                nivelDerecha = int(nivelMax * fuerza)
            if valor > 50:
                nivelDerecha = nivelMax
                fuerza: float = 1 - (valor - 50) / 50
                nivelIzquierda = int(nivelMax * fuerza)
            comando = f"pactl set-sink-volume {dispositivo} {nivelIzquierda}% {nivelDerecha}%"
        else:
            Logger.info("Opción de audio no encontrada")
            return

        accionVolumen = accionOS()
        accionVolumen.configurar({"comando": comando})
        accionVolumen.ejecutar()

        accionSalvar = accionSalvarPulse()
        accionSalvar.ejecutar()

    def obtenerPorcentajes(self, texto: str) -> list:
        return re.findall("([0-9][0-9][0-9]|[0-9][0-9]|[0-9])%", texto)


class accionMute(accion):
    """Salvar la información Dispositivo Virtuales de PulseAudio"""

    nombre = "Mutear Dispositivo"
    comando = "mute"
    descripcion = "Silencia y Activa el sonido de un dispositivo Pulse Audio"

    propiedadDispositivo: propiedadAccion = propiedadAccion(
        nombre="Dispositivo",
        tipo=str,
        obligatorio=True,
        atributo="dispositivo",
        descripcion="Nombre del dispositivo a cambiar volumen",
        ejemplo="microfono",
    )

    propiedadTipo: propiedadAccion = propiedadAccion(
        nombre="Tipo",
        tipo=str,
        obligatorio=False,
        atributo="tipo",
        descripcion="Nombre del dispositivo a cambiar volumen",
        ejemplo="sink",
        defecto="sink",
    )

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.agregarPropiedad(self.propiedadDispositivo)
        self.agregarPropiedad(self.propiedadTipo)

        self.funcion = self.cambiarMute

    def cambiarMute(self):

        dispositivo = self.obtenerValor("dispositivo")
        tipo = self.obtenerValor("tipo")

        comando = f"pactl set-{tipo}-mute {dispositivo} toggle"

        accionVolumen = accionOS()
        accionVolumen.configurar({"comando": comando})
        accionVolumen.ejecutar()

        accionSalvar = accionSalvarPulse()
        accionSalvar.ejecutar()


class accionSalvarPulse(accion):
    """Salvar la información Dispositivo Virtuales de PulseAudio"""

    nombre = "Salvar PulseAudio"
    comando = "salvar_audio"
    descripcion = "Salva información de audio virtuales"

    archivoPulse = "data/pulse.md"
    "Ruta donde se guarda la información de PulseAudio"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.funcion = self.salvarPulse

    def salvarPulse(self) -> None:
        Logger.info("Pulse[Salvar]")

        listaDispositivos: list[dispositivoSonido] = self.DataPulse()

        for Dispositivo in listaDispositivos:
            Texto = "Error"
            TextoBalance = "Error"
            if Dispositivo.mute:
                Texto = "Mute"
            elif Dispositivo.volumen is not None:
                Volumen = Dispositivo.volumen
                if Volumen[0] == Volumen[1]:
                    Texto = f"{Volumen[0]}%"
                    TextoBalance = "50%"
                else:
                    Texto = f"{Volumen[0]}% - {Volumen[1]}%"
                    if Volumen[0] == Volumen[1]:
                        TextoBalance = "50%"
                    elif Volumen[0] > Volumen[1]:
                        TextoBalance = "0%"
                    else:
                        TextoBalance = "100%"

            # TODO: montar el avanza correctamente
            SalvarValor(self.archivoPulse, f"{Dispositivo.nombre}_balance", TextoBalance)

            SalvarValor(self.archivoPulse, Dispositivo.nombre, Texto)

        self.funcionExterna()

    def DataPulse(self) -> list[dispositivoSonido]:
        Salida = sp.getoutput("pactl list sinks")
        Salida = Salida.split("Destino")
        listaDispisitovos: list[dispositivoSonido] = []
        for Data in Salida:
            Lineas = Data.split("\n")
            actual: dispositivoSonido = dispositivoSonido()
            for Linea in Lineas:
                if "Nombre:" in Linea:
                    actual.nombre = Linea.replace("Nombre:", "").strip()
                if "Volumen:" in Linea:
                    Numero = self.obtenerPorcentajes(Linea)
                    actual.volumen = Numero
                if "Silenciado:" in Linea:
                    if "sí" in Linea:
                        actual.mute = True
                    else:
                        actual.mute = False
            if actual.volumen is not None and actual.nombre is not None:
                listaDispisitovos.append(actual)

        return listaDispisitovos

    def obtenerPorcentajes(self, texto: str) -> list:
        return re.findall("([0-9][0-9][0-9]|[0-9][0-9]|[0-9])%", texto)
