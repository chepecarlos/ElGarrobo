# https://github.com/Elektordi/obs-websocket-py
import logging

from obswebsocket import obsws, requests, events
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import SalvarValor, SalvarArchivo

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class MiOBS:
    def __init__(self):
        self.host = "localhost"
        self.port = 4444

    def CambiarHost(self, Host):
        self.host = Host

    def DibujarDeck(self, Funcion):
        self.Dibujar = Funcion

    def Conectar(self):
        try:
            self.OBS = obsws(self.host, self.port)
            self.OBS.connect()
            self.Conectado = True
            logger.info(f"Conectado OBS - {self.host}")
        except Exception as e:
            logger.warning(f"Error Conectando OBS - {self.host} - {e}")
            self.Conectado = False
            return
        SalvarValor("data/obs.json", "conectado", True)
        self.SalvarEstadoActual()
        self.Evento(self.EventoEsena,  events.SwitchScenes)
        self.OBS.register(self.EventoGrabando, events.RecordingStarted)
        self.OBS.register(self.EventoGrabando, events.RecordingStopping)
        self.OBS.register(self.EventoEnVivo, events.StreamStarted)
        self.OBS.register(self.EventoEnVivo, events.StreamStopping)
        # self.OBS.register(self.EventoPrueva, events.StreamStatus)
        self.OBS.register(self.EventoSalir, events.Exiting)

        self.Dibujar()
        # self.Consultas()

    def Desconectar(self):
        logger.info(f"Desconectand OBS - {self.host}")
        SalvarValor("data/obs.json", "conectado", False)
        self.OBS.disconnect()
        self.Conectado = False

    def CambiarEsena(self, Esena):
        if self.Conectado:
            self.OBS.call(requests.SetCurrentScene(Esena))
            logger.info(f"Cambiando a Esena:{Esena}")
        else:
            logger.warning("OBS no Conectado")

    def SalvarEstadoActual(self):
        EsenaActual = self.OBS.call(requests.GetCurrentScene()).datain['name']
        EstadoActual = self.OBS.call(requests.GetStreamingStatus()).datain
        SalvarValor("data/obs.json", "esena_actual", EsenaActual)
        SalvarValor("data/obs.json", "grabando", EstadoActual['recording'])
        SalvarValor("data/obs.json", "envivo", EstadoActual['streaming'])

    def Evento(self, Funcion, Evento):
        self.OBS.register(Funcion, events.SwitchScenes)

    def EventoEsena(self, Mensaje):
        EsenaActual = Mensaje.datain['scene-name']
        SalvarValor("data/obs.json", "esena_actual", EsenaActual)
        logger.info(f"cambiando a esena:{EsenaActual}")
        self.Dibujar()

    def EventoGrabando(self, Mensaje):
        if Mensaje.name == "RecordingStarted":
            SalvarValor("data/obs.json", "grabando", True)
            logger.info("OBS Grabando")
        elif Mensaje.name == "RecordingStopping":
            SalvarValor("data/obs.json", "grabando", False)
            logger.info(f"OBS Paro Grabacion {Mensaje.datain['rec-timecode']}")
        self.Dibujar()

    def EventoSalir(self, Mensaje):
        logger.info("Se desconecto OBS")
        try:
            self.Desconectar()
        except Exception:
            pass
        SalvarArchivo("data/obs.json", dict())
        self.Dibujar()

    def EventoEnVivo(self, Mensaje):
        if Mensaje.name == "StreamStarted":
            SalvarValor("data/obs.json", "envivo", True)
            logger.info("OBS EnVivo")
        elif Mensaje.name == "StreamStopping":
            SalvarValor("data/obs.json", "envivo", False)
            logger.info(f"OBS Paro EnVivo {Mensaje.datain['stream-timecode']}")
        self.Dibujar()

    def CambiarGrabacion(self):
        if self.Conectado:
            logger.info("Cambiando estado Grabacion")
            self.OBS.call(requests.StartStopRecording())
        else:
            logger.info("OBS no Conectado")

    def CambiarEnVivo(self):
        if self.Conectado:
            logger.info("Cambiando estado EnVivo")
            self.OBS.call(requests.StartStopStreaming())
        else:
            logger.info("OBS no Conectado")

    def EventoPrueva(self, Mensaje):
        print(Mensaje)

    def Consultas(self):
        # print(dir(requests))
        print()
        print(dir(events))
        print()
