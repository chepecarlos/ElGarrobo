# https://github.com/Elektordi/obs-websocket-py
import logging

from obswebsocket import obsws, requests, events
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import SalvarValor

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class MiOBS:
    def __init__(self):
        self.host = "localhost"
        self.port = 4444

    def CambiarHost(self, Host):
        self.host = Host

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
        self.SalvarEstadoActual()

    def Desconectar(self):
        logger.info(f"Desconectand OBS - {self.host}")
        self.OBS.disconnect()
        self.Conectado = False

    def SalvarEstadoActual(self):
        EsenaActual = self.OBS.call(requests.GetCurrentScene()).datain['name']
        EstadoActual = self.OBS.call(requests.GetStreamingStatus()).datain
        SalvarValor("data/obs.json", "esena_actual", EsenaActual)
        SalvarValor("data/obs.json", "grabando", EstadoActual['recording'])
        SalvarValor("data/obs.json", "envivo", EstadoActual['streaming'])

    def Consultas(self):
        print(dir(requests))
