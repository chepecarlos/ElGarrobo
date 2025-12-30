import re
import subprocess as sp

from elGarrobo.accionesOOP.accionOS import accionOS
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor, SalvarValor

from .dispositivoSonido import dispositivoSonido
from .modulo import modulo

Logger = ConfigurarLogging(__name__)


class MiPulse(modulo):
    archivoPulse = "data/pulse.md"

    def __init__(self):
        self.SolisitarDibujar: callable = None

    def DibujarDeck(self, Funcion):
        """Guarda Funcion para Solisitar iconos StringDeck."""
        self.SolisitarDibujar = Funcion

    def IniciarAcciones(self, ListaAcciones, ListaClasesAcciones):
        ListaAcciones["mute"] = self.CambiarMute
        ListaAcciones["salvar_pulse"] = self.SalvarPulse

    def cambiarVolumen(self, opcion) -> None:

        dispositivo = self.obtenerValor(opcion, "dispositivo")
        valor = self.obtenerValor(opcion, "valor")
        opcion = self.obtenerValor(opcion, "opcion")

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

        self.SalvarPulse()

    def CambiarMute(self, opciones):

        Dispositivo = None
        Tipo = "sink"

        if "tipo" in opciones:
            Tipo = opciones["tipo"]
        if "dispositivo" in opciones:
            Dispositivo = opciones["dispositivo"]

        if Dispositivo is None:
            Logger.info("Necesario de dispositivo")
            return

        comando = f"pactl set-{Tipo}-mute {Dispositivo} toggle"

        accionVolumen = accionOS()
        accionVolumen.configurar({"comando": comando})
        accionVolumen.ejecutar()

        self.SalvarPulse()

    def SalvarPulse(self, opciones=None):
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

        self.SolisitarDibujar()

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
