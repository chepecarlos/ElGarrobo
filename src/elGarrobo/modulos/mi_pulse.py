import re
import subprocess as sp

from elGarrobo.accionesOOP.accionOS import accionOS
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor, SalvarValor

Logger = ConfigurarLogging(__name__)


class MiPulse:
    archivoPulse = "data/pulse.md"

    def __init__(self):
        self.SolisitarDibujar: callable = None

    def DibujarDeck(self, Funcion):
        """Guarda Funcion para Solisitar iconos StringDeck."""
        self.SolisitarDibujar = Funcion

    def IniciarAcciones(self, ListaAcciones, ListaClasesAcciones):
        ListaAcciones["volumen"] = self.CambiarVolumen
        ListaAcciones["mute"] = self.CambiarMute
        ListaAcciones["salvar_pulse"] = self.SalvarPulse

    def CambiarVolumen(self, opciones):

        Dispositivo = opciones.get("dispositivo")
        Valor = opciones.get("valor")
        Opcion = opciones.get("opcion", "asigniar")
        comando = None

        if Dispositivo is None or Valor is None:
            Logger.info("Faltan opciones")
            return

        if Opcion == "asignar":
            comando = f"pactl set-sink-volume {Dispositivo} {Valor}%"
        elif Opcion == "incremento":
            simbolo = "+" if Valor > 0 else ""
            comando = f"pactl set-sink-volume {Dispositivo} {simbolo}{Valor}%"
        elif Opcion == "balance":
            texto: str = ObtenerValor(self.archivoPulse, Dispositivo)
            if texto is None:
                Logger.warning(f"Error con Disposition {Dispositivo}")
                return

            nivel: str = self.obtenerPorcentajes(texto)
            if nivel is None:
                Logger.warning(f"Error con Nivel de Disposition {Dispositivo}")
                return
            nivelIzquierda: int = 0
            nivelDerecha: int = 0
            if len(nivel) == 1:
                nivelMax = nivel[0]
            else:
                nivelMax = nivel[0] if nivel[0] > nivel[1] else nivel[1]
            nivelMax: int = int(nivelMax)
            if Valor == 50:
                nivelIzquierda = nivelMax
                nivelDerecha = nivelMax
            if Valor < 50:
                nivelIzquierda = nivelMax
                fuerza: float = 1 - (50 - Valor) / 50
                nivelDerecha = int(nivelMax * fuerza)
            if Valor > 50:
                nivelDerecha = nivelMax
                fuerza: float = 1 - (Valor - 50) / 50
                nivelIzquierda = int(nivelMax * fuerza)
            comando = f"pactl set-sink-volume {Dispositivo} {nivelIzquierda}% {nivelDerecha}%"
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

        listaDispisitovos: list = self.DataPulse()

        for Dispositivo in listaDispisitovos:
            Texto = "Error"
            TextoBalance = "Error"
            if Dispositivo.Mute:
                Texto = "Mute"
            elif Dispositivo.Volumen is not None:
                Volumen = Dispositivo.Volumen
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
            SalvarValor(self.archivoPulse, f"{Dispositivo.Nombre}_balance", TextoBalance)

            SalvarValor(self.archivoPulse, Dispositivo.Nombre, Texto)

        self.SolisitarDibujar()

    def DataPulse(self):
        Salida = sp.getoutput("pactl list sinks")
        Salida = Salida.split("Destino")
        listaDispisitovos = []
        for Data in Salida:
            Lineas = Data.split("\n")
            actual = Dispositivo()
            for Linea in Lineas:
                if "Nombre:" in Linea:
                    actual.Nombre = Linea.replace("Nombre:", "").strip()
                if "Volumen:" in Linea:
                    Numero = self.obtenerPorcentajes(Linea)
                    actual.Volumen = Numero
                if "Silencio:" in Linea:
                    if "sí" in Linea:
                        actual.Mute = True
                    else:
                        actual.Mute = False
            if actual.Volumen is not None:
                listaDispisitovos.append(actual)

        return listaDispisitovos

    def obtenerPorcentajes(self, texto: str) -> list:
        return re.findall("([0-9][0-9][0-9]|[0-9][0-9]|[0-9])%", texto)


class Dispositivo(object):
    Nombre = None
    Volumen = [0, 0]
    Mute = None
