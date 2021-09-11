# Libreria: https://github.com/Elektordi/obs-websocket-py
import threading

from obswebsocket import obsws, requests, events

from MiLibrerias import ConfigurarLogging
from MiLibrerias import SalvarValor, SalvarArchivo, ObtenerValor

logger = ConfigurarLogging(__name__)


class MiOBS:
    """Coneccion con OBS."""

    def __init__(self):
        """Crea coneccion basica con OBS Websocket."""
        logger.info("OBS[Iniciando]")
        self.Reiniciar()

    def Reiniciar(self):
        self.host = "localhost"
        self.port = 4444
        self.Conectado = False
        SalvarValor("data/obs.json", "obs_conectar", False)
        self.LimpiarTemporales()

    def CambiarHost(self, Host):
        """Cambia el host a conectarse."""
        self.host = Host

    def DibujarDeck(self, Funcion):
        """Guarda Funcion para refrescar iconos StringDeck."""
        self.Dibujar = Funcion

    def Conectar(self, Opciones):
        """Se conecta a OBS Websocket y inicializa los eventos."""
        try:
            self.OBS = obsws(self.host, self.port)
            self.OBS.connect()
            self.Conectado = True
            logger.info(f"OBS[Conectado] {self.host}")
        except Exception as error:
            logger.warning(f"OBS[Error] {error}")
            self.LimpiarTemporales()
            self.Conectado = False
            SalvarValor("data/obs.json", "obs_conectar", False)
            return
        self.SalvarEstadoActual()
        self.AgregarEvento(self.EventoEscena, events.SwitchScenes)
        self.AgregarEvento(self.EventoGrabando, events.RecordingStarted)
        self.AgregarEvento(self.EventoGrabando, events.RecordingStopping)
        self.AgregarEvento(self.EventoEnVivo, events.StreamStarted)
        self.AgregarEvento(self.EventoEnVivo, events.StreamStopping)
        self.AgregarEvento(self.EventoVisibilidadIten,
                           events.SceneItemVisibilityChanged)
        self.AgregarEvento(self.EventoVisibilidadFiltro,
                           events.SourceFilterVisibilityChanged)
        self.AgregarEvento(self.EventoSalir, events.Exiting)
        self.Dibujar()

    def SalvarEstadoActual(self):
        """Salta estado inicial de OBS para StreamDeck."""
        DataEscenaActual = self.OBS.call(requests.GetCurrentScene()).datain
        EstadoActual = self.OBS.call(requests.GetStreamingStatus()).datain
        SalvarValor("data/obs.json", "obs_conectar", self.Conectado)
        SalvarValor("data/obs.json", "obs_escena", DataEscenaActual['name'])
        SalvarValor("data/obs.json", "obs_grabar", EstadoActual['recording'])
        SalvarValor("data/obs.json", "obs_envivo", EstadoActual['streaming'])

        self.SalvarFuente()

    def SalvarFuente(self):
        HiloFuentes = threading.Thread(target=self.HiloFuenteArchivo)
        HiloFuentes.start()

    def HiloFuenteArchivo(self):
        DataEscenaActual = self.OBS.call(requests.GetCurrentScene()).datain
        Refrescar = False
        for Fuente in DataEscenaActual['sources']:
            NombreFuente = Fuente['name']
            EstadoFuente = ObtenerValor(
                "data/obs_fuente.json", NombreFuente, Depurar=False)
            EstadoFuenteActual = self.OBS.call(
                requests.GetSceneItemProperties(NombreFuente)).datain
            if 'visible' in EstadoFuenteActual:
                EstadoFuenteActual = EstadoFuenteActual['visible']
                if EstadoFuente is not None:
                    if EstadoFuente != EstadoFuenteActual:
                        self.CambiarFuente(Fuente=NombreFuente)
                        Refrescar = True
                else:
                    SalvarValor("data/obs_fuente.json",
                                NombreFuente, EstadoFuenteActual)
                    Refrescar = True
            self.SalvarFiltroFuente(NombreFuente)

        if Refrescar:
            self.Dibujar()

    def AgregarEvento(self, Funcion, Evento):
        """Registra evento de OBS a una funcion."""
        self.OBS.register(Funcion, Evento)

    def EventoEscena(self, Mensaje):
        """Recive nueva escena actual."""
        EscenaActual = Mensaje.datain['scene-name']
        SalvarValor("data/obs.json", "obs_escena", EscenaActual)
        logger.info(f"OBS[Escena] {EscenaActual}")
        self.SalvarFuente()
        self.Dibujar()

    def EventoGrabando(self, Mensaje):
        """Recive estado de grabacion."""
        if Mensaje.name == "RecordingStarted":
            SalvarValor("data/obs.json", "obs_grabar", True)
            logger.info("OBS[Grabando]")
        elif Mensaje.name == "RecordingStopping":
            SalvarValor("data/obs.json", "obs_grabar", False)
            logger.info(f"OBS[Grabo] {Mensaje.datain['rec-timecode']}")
        self.Dibujar()

    def EventoEnVivo(self, Mensaje):
        """Recive estado del Striming."""
        if Mensaje.name == "StreamStarted":
            SalvarValor("data/obs.json", "obs_envivo", True)
            logger.info("OBS EnVivo")
        elif Mensaje.name == "StreamStopping":
            SalvarValor("data/obs.json", "obs_envivo", False)
            logger.info(f"OBS Paro EnVivo {Mensaje.datain['stream-timecode']}")
        self.Dibujar()

    def EventoSalir(self, Mensaje):
        """Recive desconeccion de OBS websocket."""
        logger.info("Se desconecto OBS")
        try:
            self.Desconectar()
        except Exception as Error:
            logger.warning(f"OBS[Error] {Error}")
        self.LimpiarTemporales()
        self.Dibujar()

    def EventoVisibilidadIten(self, Mensaje):
        """Recive estado de fuente."""
        NombreFuente = Mensaje.datain['item-name']
        Visibilidad = Mensaje.datain['item-visible']
        logger.info(f"OBS[{NombreFuente}] {Visibilidad}")
        SalvarValor("data/obs_fuente.json", NombreFuente, Visibilidad)
        self.Dibujar()

    def EventoVisibilidadFiltro(self, Mensaje):
        """Recive estado del filtro."""
        NombreFiltro = Mensaje.datain['filterName']
        NombreFuente = Mensaje.datain['sourceName']
        Visibilidad = Mensaje.datain['filterEnabled']
        logger.info(f"OBS[{NombreFiltro}] {Visibilidad}")
        Data = list()
        Data.append(NombreFuente)
        Data.append(NombreFiltro)
        SalvarValor("data/obs_filtro.json", Data, Visibilidad)
        self.Dibujar()

    def SalvarFiltroFuente(self, Fuente):
        """Salva el estado de los filtros de una fuente."""
        DataFuente = self.OBS.call(requests.GetSourceFilters(Fuente))

        ListaFiltros = DataFuente.datain['filters']
        if ListaFiltros is not None:
            for Filtro in ListaFiltros:
                NombreFiltro = Filtro['name']
                Data = [Fuente, NombreFiltro, "enabled"]

                SalvarValor("data/obs_filtro.json",
                            [Fuente, NombreFiltro], Filtro['enabled'])

                SalvarValor("data/obs_filtro_opciones.json",
                            Data, Filtro['enabled'])

                Data = [Fuente, NombreFiltro, "type"]
                SalvarValor("data/obs_filtro_opciones.json",
                            Data, Filtro['type'])
                self.SalvarFiltroConfiguraciones(Data[:-1], Filtro['settings'])

    def SalvarFiltroConfiguraciones(self, Filtro, lista):
        for elemento in lista:
            Data = Filtro.copy()
            Data.append(elemento)
            SalvarValor("data/obs_filtro_opciones.json", Data, lista[elemento])

    def CambiarEscena(self, Opciones):
        """Envia solisitud de cambiar de Escena."""
        if 'escena' in Opciones:
            Escena = Opciones['escena']
        else:
            logger.info(f"esena no definida")
            return

        if self.Conectado:
            self.OBS.call(requests.SetCurrentScene(Escena))
            logger.info(f"OBS[Cambiando] {Escena}")
        else:
            logger.warning("OBS[No conectado]")

    def CambiarFuente(self, Opciones=False, Fuente=None):
        """Envia solisitud de Cambia el estado de una fuente."""
        if Fuente is None:
            if 'fuente' in Opciones:
                Fuente = Opciones['fuente']

        if self.Conectado:
            Estado = ObtenerValor("data/obs_fuente.json", Fuente)

            if Estado is not None:
                Estado = not Estado
                logger.info(f"OBS[Fuente] {Fuente}={Estado}")
                self.OBS.call(requests.SetSceneItemProperties(
                    Fuente, visible=Estado))
            else:
                logger.warning(
                    f"No se encontro {Fuente[0]} o {Fuente[1]} en OBS")

        else:
            logger.info("OBS[no Conectado]")

    def CambiarFiltro(self, Opciones):
        """Envia solisitud de cambiar estado de filtro."""
        Filtro = None
        Fuente = None
        if 'filtro' in Opciones:
            Filtro = Opciones['filtro']
        if 'fuente' in Opciones:
            Fuente = Opciones['fuente']

        if Filtro is None or Fuente is None:
            logger.info("OBS[Falta Atributo]")
            return

        if self.Conectado:
            Estado = ObtenerValor("data/obs_filtro.json", [Fuente, Filtro])
            if Estado is not None:
                Estado = not Estado
                logger.info(
                    f"OBS[Filtro] {Fuente}-{Fuente}={Estado}")
                self.OBS.call(requests.SetSourceFilterVisibility(
                    Fuente, Filtro, Estado))
        else:
            logger.info("OBS[no Conectado]")

    def CambiarGrabacion(self, Opciones=None):
        """Envia solisitud de cambiar estado de Grabacion."""
        if self.Conectado:
            logger.info("Cambiando[Grabacion]")
            self.OBS.call(requests.StartStopRecording())
        else:
            logger.info("OBS no Conectado")
        return

    def CambiarEnVivo(self, Opciones=None):
        """Envia solisitud de cambiar estado del Streaming ."""
        if self.Conectado:
            logger.info("Cambiando estado EnVivo")
            self.OBS.call(requests.StartStopStreaming())
        else:
            logger.info("OBS no Conectado")

    def LimpiarTemporales(self):
        """Limpia los archivos con informacion temporal de OBS."""
        SalvarArchivo("data/obs.json", dict())
        SalvarArchivo("data/obs_fuente.json", dict())
        SalvarArchivo("data/obs_filtro.json", dict())
        SalvarArchivo("data/obs_filtro_opciones.json", dict())

    def Desconectar(self, Opciones=False):
        """Deconectar de OBS websocket."""
        logger.info(f"OBS[Desconectar] - {self.host}")
        if self.Conectado:
            self.OBS.disconnect()
            self.LimpiarTemporales()
        self.Conectado = False
        SalvarValor("data/obs.json", "obs_conectar", False)
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
