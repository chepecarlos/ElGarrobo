import subprocess as sp
import re

from acciones.accion_os import AccionOS
import logging
from MiLibrerias import ConfigurarLogging
from MiLibrerias import ObtenerValor, SalvarValor

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

    def CambiarVolumen(self, Opciones):

        Dispositivo = None
        Valor = None
        Opcion = "asigniar"
        comando = None

        if "dispositivo" in Opciones:
            Dispositivo = Opciones["dispositivo"]
        if "valor" in Opciones:
            Valor = Opciones["valor"]
        if "opcion" in Opciones:
            Opcion = Opciones["opcion"]

        if Dispositivo is None or Valor is None:
            logging.info("Faltan opciones")
            return

        if Opcion == "asignar":
            comando = f"pactl set-sink-volume {Dispositivo} {Valor}%"
        elif Opcion == "incremento":
            simbolo = "+" if Valor > 0 else ""
            comando = f"pactl set-sink-volume {Dispositivo} {simbolo}{Valor}%"
        else:
            logging.info("Opcion de audio no enocntrada")
            return

        AccionOS({"comando": comando})
        self.SalvarPulse()

    def CambiarMute(self, Opciones):

        Dispositivo = None
        Tipo = "sink"

        if "tipo" in Opciones:
            Tipo = Opciones["tipo"]
        if "dispositivo" in Opciones:
            Dispositivo = Opciones["dispositivo"]

        if Dispositivo == None:
            Logger.info("Necesario de dispositivo")
            return

        comando = f"pactl set-{Tipo}-mute {Dispositivo} toggle"

        AccionOS({"comando": comando})
        self.SalvarPulse()

    def SalvarPulse(self, Opciones=None):
        Logger.info("Pulse[Salvar]")

        ListaDispisitovos = self.DataPulse()

        for Dispositivo in ListaDispisitovos:
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
        ListaDispisitovos = []
        for Data in Salida:
            Lineas = Data.split("\n")
            Actual = Dispositivo()
            for Linea in Lineas:
                if "Nombre:" in Linea:
                    Actual.Nombre = Linea.replace("Nombre:", "").strip()
                if "Volumen:" in Linea:
                    Numero = re.findall("([0-9][0-9][0-9]|[0-9][0-9]|[0-9])%", Linea)
                    Actual.Volumen = Numero[0]
                if "Silencio:" in Linea:
                    if "sí" in Linea:
                        Actual.Mute = True
                    else:
                        Actual.Mute = False
            if Actual.Volumen is not None:
                ListaDispisitovos.append(Actual)

        return ListaDispisitovos


class Dispositivo(object):
    Nombre = None
    Volumen = None
    Mute = None
