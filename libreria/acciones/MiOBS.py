# https://github.com/Elektordi/obs-websocket-py
import logging
import threading

from obswebsocket import obsws, requests, events
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import SalvarValor, SalvarArchivo, ObtenerValor


logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class MiOBS:
    """Coneccion con OBS."""

    def __init__(self):
        """Crea coneccion basica con OBS Websocket."""
        self.host = "localhost"
        self.port = 4444
        self.Conectado = False
        self.LimpiarTemporales()

    def CambiarHost(self, Host):
        """Cambia el host a conectarse."""
        self.host = Host

    def DibujarDeck(self, Funcion):
        """Guarda Funcion para refrescar iconos StringDeck."""
        self.Dibujar = Funcion

    def Conectar(self):
        """Se conecta a OBS Websocket y inicializa los eventos."""
        try:
            self.OBS = obsws(self.host, self.port)
            self.OBS.connect()
            self.Conectado = True
            logger.info(f"Conectado OBS - {self.host}")
        except Exception as e:
            logger.warning(f"Error Conectando OBS - {self.host} - {e}")
            self.LimpiarTemporales()
            self.Conectado = False
            return
        SalvarValor("data/obs.json", "conectado", True)
        self.SalvarEstadoActual()
        self.AgregarEvento(self.EventoEsena, events.SwitchScenes)
        self.AgregarEvento(self.EventoGrabando, events.RecordingStarted)
        self.AgregarEvento(self.EventoGrabando, events.RecordingStopping)
        self.AgregarEvento(self.EventoEnVivo, events.StreamStarted)
        self.AgregarEvento(self.EventoEnVivo, events.StreamStopping)
        self.AgregarEvento(self.EventoVisibilidadIten, events.SceneItemVisibilityChanged)
        self.AgregarEvento(self.EventoVisibilidadFiltro, events.SourceFilterVisibilityChanged)
        self.AgregarEvento(self.EventoSalir, events.Exiting)
        self.Dibujar()

    def SalvarEstadoActual(self):
        """Salta estado inicial de OBS para StreamDeck."""
        DataEsenaActual = self.OBS.call(requests.GetCurrentScene()).datain
        EstadoActual = self.OBS.call(requests.GetStreamingStatus()).datain
        SalvarValor("data/obs.json", "esena_actual", DataEsenaActual['name'])
        SalvarValor("data/obs.json", "grabando", EstadoActual['recording'])
        SalvarValor("data/obs.json", "envivo", EstadoActual['streaming'])
        self.SalvarFuente()

    def SalvarFuente(self):
        HiloFuentes = threading.Thread(target=self.HiloFuenteArchivo)
        HiloFuentes.start()

    def HiloFuenteArchivo(self):
        DataEsenaActual = self.OBS.call(requests.GetCurrentScene()).datain
        Refrescar = False
        for Fuente in DataEsenaActual['sources']:
            NombreFuente = Fuente['name']
            EstadoFuente = ObtenerValor("data/fuente_obs.json", NombreFuente)
            EstadoFuenteActual = self.OBS.call(requests.GetSceneItemProperties(NombreFuente)).datain
            if 'visible' in EstadoFuenteActual:
                EstadoFuenteActual = EstadoFuenteActual['visible']
                if EstadoFuente is not None:
                    if EstadoFuente != EstadoFuenteActual:
                        self.CambiarFuente(NombreFuente, EstadoFuente)
                        Refrescar = True
                else:
                    SalvarValor("data/fuente_obs.json", NombreFuente, EstadoFuenteActual)
                    Refrescar = True

        if Refrescar:
            self.Dibujar()

    def AgregarEvento(self, Funcion, Evento):
        """Registra evento de OBS a una funcion."""
        self.OBS.register(Funcion, Evento)

    def EventoEsena(self, Mensaje):
        """Recive nueva esena actual."""
        EsenaActual = Mensaje.datain['scene-name']
        SalvarValor("data/obs.json", "esena_actual", EsenaActual)
        logger.info(f"Evento a esena: {EsenaActual}")
        self.SalvarFuente()
        self.Dibujar()

    def EventoGrabando(self, Mensaje):
        """Recive estado de grabacion."""
        if Mensaje.name == "RecordingStarted":
            SalvarValor("data/obs.json", "grabando", True)
            logger.info("OBS Grabando")
        elif Mensaje.name == "RecordingStopping":
            SalvarValor("data/obs.json", "grabando", False)
            logger.info(f"OBS Paro Grabacion {Mensaje.datain['rec-timecode']}")
        self.Dibujar()

    def EventoEnVivo(self, Mensaje):
        """Recive estado del Striming."""
        if Mensaje.name == "StreamStarted":
            SalvarValor("data/obs.json", "envivo", True)
            logger.info("OBS EnVivo")
        elif Mensaje.name == "StreamStopping":
            SalvarValor("data/obs.json", "envivo", False)
            logger.info(f"OBS Paro EnVivo {Mensaje.datain['stream-timecode']}")
        self.Dibujar()

    def EventoSalir(self, Mensaje):
        """Recive desconeccion de OBS websocket."""
        logger.info("Se desconecto OBS")
        try:
            self.Desconectar()
        except Exception:
            pass
        self.LimpiarTemporales()
        self.Dibujar()

    def EventoVisibilidadIten(self, Mensaje):
        """Recive estado de fuente."""
        NombreFuente = Mensaje.datain['item-name']
        Visibilidad = Mensaje.datain['item-visible']
        logger.info(f"Cambiano Visibilidad {NombreFuente} - {Visibilidad}")
        SalvarValor("data/fuente_obs.json", NombreFuente, Visibilidad)
        self.Dibujar()

    def EventoVisibilidadFiltro(self, Mensaje):
        """Recive estado del filtro."""
        NombreFiltro = Mensaje.datain['filterName']
        NombreFuente = Mensaje.datain['sourceName']
        Visibilidad = Mensaje.datain['filterEnabled']
        logger.info(f"Cambiando Visibilidad {NombreFuente}[{NombreFiltro}] - {Visibilidad}")
        Data = list()
        Data.append(NombreFuente)
        Data.append(NombreFiltro)
        SalvarValor("data/filtro_obs.json", Data, Visibilidad)
        self.Dibujar()

    def CambiarEsena(self, Esena):
        """Envia solisitud de cambiar de Esena."""
        if self.Conectado:
            self.OBS.call(requests.SetCurrentScene(Esena))
            logger.info(f"Cambiando a Esena: {Esena}")
        else:
            logger.warning("OBS no Conectado")

    def CambiarFuente(self, Fuente, Estado):
        """Envia solisitud de cambiar estado de fuente."""
        if self.Conectado:
            logger.info(f"Cambiando Fuente {Fuente} - {Estado}")
            self.OBS.call(requests.SetSceneItemProperties(Fuente, visible=Estado))
        else:
            logger.info("OBS no Conectado")

    def CambiarFiltro(self, Fuente, Filtro, Estado):
        """Envia solisitud de cambiar estado de filtro."""
        if self.Conectado:
            logger.info(f"Cambiando Filtro {Filtro} de {Fuente} a {Estado}")
            self.OBS.call(requests.SetSourceFilterVisibility(Fuente, Filtro, Estado))
        else:
            logger.info("OBS no Conectado")

    def CambiarGrabacion(self):
        """Envia solisitud de cambiar estado de Grabacion."""
        if self.Conectado:
            logger.info("Cambiando estado Grabacion")
            self.OBS.call(requests.StartStopRecording())
        else:
            logger.info("OBS no Conectado")

    def CambiarEnVivo(self):
        """Envia solisitud de cambiar estado del Streaming ."""
        if self.Conectado:
            logger.info("Cambiando estado EnVivo")
            self.OBS.call(requests.StartStopStreaming())
        else:
            logger.info("OBS no Conectado")

    def LimpiarTemporales(self):
        """Limpia los archivos con informacion temporal de OBS."""
        SalvarArchivo("data/obs.json", dict())
        SalvarArchivo("data/fuente_obs.json", dict())
        SalvarArchivo("data/filtro_obs.json", dict())

    def Desconectar(self):
        """Deconectar de OBS websocket."""
        logger.info(f"Desconectand OBS - {self.host}")
        self.Conectado = False
        self.LimpiarTemporales()
        self.OBS.disconnect()
        self.Dibujar()

    def __del__(self):
        """Borrar objeto de Websocket ."""
        self.Desconectar()

    def EventoPrueva(self, Mensaje):
        print(Mensaje)

    def Consultas(self):
        # print(dir(requests))
        print()
        print(dir(events))
        print()
