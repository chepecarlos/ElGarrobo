# https://github.com/Elektordi/obs-websocket-py
import logging

from obswebsocket import obsws, requests, events
from libreria.FuncionesLogging import ConfigurarLogging

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
            logger.info(f"Intentando Conectar con {self.host}")
            self.OBS = obsws(self.host, self.port)
            self.OBS.connect()
            self.Conectado = True
        except Exception as e:
            logger.warning(f"No se pudo conectar a OBS {e}")
            self.Conectado = False

    def Desconectar(self):
        self.OBS.disconnect()
