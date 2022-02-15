import re
import subprocess as sp

from acciones.accion_os import accionOS
from MiLibrerias import ConfigurarLogging, ObtenerValor, SalvarValor

Logger = ConfigurarLogging(__name__)


class MiPulse:
    def __init__(self):
        self.SolisitarDibujar = None

    def DibujarDeck(self, Funcion):
        """Guarda Funcion para Solisitar iconos StringDeck."""
        self.SolisitarDibujar = Funcion

    def IniciarAcciones(self, ListaAcciones):
        ListaAcciones["volumen"] = self.CambiarVolumen
        ListaAcciones["mute"] = self.CambiarMute
        ListaAcciones["salvar_pulse"] = self.SalvarPulse

    def CambiarVolumen(self, opciones):

        Dispositivo = None
        Valor = None
        Opcion = "asigniar"
        comando = None

        if "dispositivo" in opciones:
            Dispositivo = opciones["dispositivo"]
        if "valor" in opciones:
            Valor = opciones["valor"]
        if "opcion" in opciones:
            Opcion = opciones["opcion"]

        if Dispositivo is None or Valor is None:
            Logger.info("Faltan opciones")
            return

        if Opcion == "asignar":
            comando = f"pactl set-sink-volume {Dispositivo} {Valor}%"
        elif Opcion == "incremento":
            simbolo = "+" if Valor > 0 else ""
            comando = f"pactl set-sink-volume {Dispositivo} {simbolo}{Valor}%"
        else:
            Logger.info("Opción de audio no encontrada")
            return

        accionOS({"comando": comando})
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

        accionOS({"comando": comando})
        self.SalvarPulse()

    def SalvarPulse(self, opciones=None):
        Logger.info("Pulse[Salvar]")

        listaDispisitovos = self.DataPulse()

        for Dispositivo in listaDispisitovos:
            Texto = "Error"
            if Dispositivo.Mute:
                Texto = "Mute"
            elif Dispositivo.Volumen is not None:
                Texto = f"{Dispositivo.Volumen}%"

            SalvarValor("data/pulse.json", Dispositivo.Nombre, Texto)

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
                    Numero = re.findall("([0-9][0-9][0-9]|[0-9][0-9]|[0-9])%", Linea)
                    actual.Volumen = Numero[0]
                if "Silencio:" in Linea:
                    if "sí" in Linea:
                        actual.Mute = True
                    else:
                        actual.Mute = False
            if actual.Volumen is not None:
                listaDispisitovos.append(actual)

        return listaDispisitovos


class Dispositivo(object):
    Nombre = None
    Volumen = None
    Mute = None
