# Libreria: https://github.com/Elektordi/obs-websocket-py
import threading

from MiLibrerias import ConfigurarLogging, ObtenerArchivo, ObtenerValor, SalvarArchivo, SalvarValor
from obswebsocket import events, obsws, requests

logger = ConfigurarLogging(__name__)


class MiOBS:
    """Concepción con OBS."""

    def __init__(self):
        """Crea confección básica con OBS Websocket."""
        logger.info("OBS[Iniciando]")
        self.archivoEstado = "data/obs.json"
        self.Reiniciar()

    def Reiniciar(self):
        self.host = "localhost"
        self.port = 4444
        self.password = None
        self.Conectado = False
        self.Dibujar = None
        self.Notificaciones = None
        SalvarValor(self.archivoEstado, "obs_conectar", False)
        self.LimpiarTemporales()

    def CambiarHost(self, Host):
        """Cambia el host a conectarse."""
        self.host = Host

    def IniciarAcciones(self, ListaAcciones):
        ListaAcciones["obs_conectar"] = self.Conectar
        ListaAcciones["obs_desconectar"] = self.Desconectar
        ListaAcciones["obs_grabar"] = self.CambiarGrabacion
        ListaAcciones["obs_envivo"] = self.CambiarEnVivo
        ListaAcciones["obs_camara_virtual"] = self.CambiarCamaraVirtual
        ListaAcciones["obs_escena"] = self.CambiarEscena
        ListaAcciones["obs_fuente"] = self.CambiarFuente
        ListaAcciones["obs_filtro"] = self.CambiarFiltro
        ListaAcciones["obs_estado"] = self.EstadoOBS
        ListaAcciones["obs_tiempo_grabando"] = self.TiempoGrabando
        ListaAcciones["obs_tiempo_envivo"] = self.TiempoEnVivo
        # ListaAcciones['obs_host'] = self.OBS.Conectar
        # ListaAcciones['obs_server'] = self.OBS.Conectar

    def DibujarDeck(self, Funcion):
        """Guarda Funcion para refrescar iconos StringDeck."""
        self.Dibujar = Funcion

    def actualizarDeck(self):
        """Dibuja en StreanDeck si es posible"""
        if self.Dibujar is not None:
            self.Dibujar()

    def AgregarNotificacion(self, Funcion):
        """Agrega función para notificación."""
        self.alertaOBS = ObtenerArchivo("modulos/alerta_obs/mqtt.json")
        self.Notificaciones = Funcion
        self.EstadoOBS({})

    def Conectar(self, opciones):
        """Se conecta a OBS Websocket y inicializa los eventos."""

        if "servidor" in opciones:
            self.host = opciones["servidor"]
        if "puerto" in opciones:
            self.port = opciones["puerto"]
        if "contrasenna" in opciones:
            self.password = opciones["contrasenna"]

        if self.Conectado:
            logger.info("OBS Ya Conectado")
            self.Notificar("OBS-Ya-Conectado")
            return

        try:
            if self.password is None:
                self.OBS = obsws(self.host, self.port)
            else:
                self.OBS = obsws(self.host, self.port, self.password)

            self.OBS.connect()
            self.Conectado = True
            logger.info(f"OBS[Conectado] {self.host}")
            self.Notificar("OBS-Conectado")
        except Exception as error:
            logger.warning(f"OBS[Error] {error}")
            self.LimpiarTemporales()
            self.Conectado = False
            SalvarValor("data/obs.json", "obs_conectar", False)
            self.Notificar("OBS-No-Encontrado")
            return
        self.SalvarEstadoActual()
        # self.OBS.call(requests.SetHeartbeat(True))
        self.AgregarEvento(self.EventoEscena, events.SwitchScenes)
        self.AgregarEvento(self.EventoGrabando, events.RecordingStarted)
        self.AgregarEvento(self.EventoGrabando, events.RecordingStopping)
        self.AgregarEvento(self.EventoEnVivo, events.StreamStarted)
        self.AgregarEvento(self.EventoEnVivo, events.StreamStopping)
        self.AgregarEvento(self.EventoVisibilidadIten, events.SceneItemVisibilityChanged)
        self.AgregarEvento(self.EventoVisibilidadFiltro, events.SourceFilterVisibilityChanged)
        self.AgregarEvento(self.EventoSalir, events.Exiting)
        # self.AgregarEvento(self.EventoPulsoCorazon, events.Heartbeat)
        self.actualizarDeck()

    def SalvarEstadoActual(self):
        """Salta estado inicial de OBS para StreamDeck."""
        DataEscenaActual = self.OBS.call(requests.GetCurrentScene()).datain
        EstadoActual = self.OBS.call(requests.GetStreamingStatus()).datain
        SalvarValor("data/obs.json", "obs_conectar", self.Conectado)
        SalvarValor("data/obs.json", "obs_escena", DataEscenaActual["name"])
        SalvarValor("data/obs.json", "obs_grabar", EstadoActual["recording"])
        SalvarValor("data/obs.json", "obs_envivo", EstadoActual["streaming"])

        self.SalvarFuente()

    def SalvarFuente(self):
        HiloFuentes = threading.Thread(target=self.HiloFuenteArchivo)
        HiloFuentes.start()

    def HiloFuenteArchivo(self):
        DataEscenaActual = self.OBS.call(requests.GetCurrentScene()).datain
        Refrescar = False
        for Fuente in DataEscenaActual["sources"]:
            NombreFuente = Fuente["name"]
            EstadoFuente = ObtenerValor("data/obs_fuente.json", NombreFuente, Depurar=False)
            EstadoFuenteActual = self.OBS.call(requests.GetSceneItemProperties(NombreFuente)).datain
            if "visible" in EstadoFuenteActual:
                EstadoFuenteActual = EstadoFuenteActual["visible"]
                if EstadoFuente is not None:
                    if EstadoFuente != EstadoFuenteActual:
                        self.CambiarFuente(Fuente=NombreFuente)
                        Refrescar = True
                else:
                    SalvarValor("data/obs_fuente.json", NombreFuente, EstadoFuenteActual)
                    Refrescar = True
            self.SalvarFiltroFuente(NombreFuente)

        if Refrescar:
            self.actualizarDeck()

    def AgregarEvento(self, Funcion, Evento):
        """Registra evento de OBS a una funcion."""
        self.OBS.register(Funcion, Evento)

    def EventoEscena(self, Mensaje):
        """Recibe nueva escena actual."""
        EscenaActual = Mensaje.datain["scene-name"]
        SalvarValor("data/obs.json", "obs_escena", EscenaActual)
        logger.info(f"OBS[Escena] {EscenaActual}")
        self.SalvarFuente()
        self.actualizarDeck()

    def EventoGrabando(self, Mensaje):
        """Recibe estado de grabación."""
        if Mensaje.name == "RecordingStarted":
            SalvarValor("data/obs.json", "obs_grabar", True)
            self.Notificar("OBS-Grabando")
            logger.info("OBS[Grabando]")
        elif Mensaje.name == "RecordingStopping":
            self.Notificar("OBS-No-Grabando")
            SalvarValor("data/obs.json", "obs_grabar", False)
            logger.info(f"OBS[Grabo] {Mensaje.datain['rec-timecode']}")
        self.actualizarDeck()

    def EventoEnVivo(self, Mensaje):
        """Recibe estado del Striming."""
        if Mensaje.name == "StreamStarted":
            SalvarValor("data/obs.json", "obs_envivo", True)
            logger.info("OBS[EnVivo]")
            self.Notificar("OBS-EnVivo")
        elif Mensaje.name == "StreamStopping":
            SalvarValor("data/obs.json", "obs_envivo", False)
            logger.info(f"OBS[Paro EnVivo] - {Mensaje.datain['stream-timecode']}")
            self.Notificar("OBS-No-EnVivo")
        self.actualizarDeck()

    def EventoSalir(self, Mensaje):
        """Recibe desconeccion de OBS websocket."""
        logger.info("OBS[Desconectado]")
        self.Notificar("OBS-No-Conectado")
        try:
            self.Desconectar()
        except Exception as Error:
            logger.warning(f"OBS[Error] {Error}")
            self.Conectado = False
        self.LimpiarTemporales()
        self.actualizarDeck()

    def EventoPulsoCorazon(self, Mensaje):
        if Mensaje.name == "Heartbeat":
            logger.info("Pulso de OBS")
            # print(Mensaje.datain)
            # if "current-profile" in Mensaje.datain:
            #     print(Mensaje.datain["current-profile"])
            # if "rec-timecode" in Mensaje.datain:
            #     print("Grabando", Mensaje.datain["rec-timecode"])
            # if "stream-timecode" in Mensaje.datain:
            #     print("EnVivo", Mensaje.datain["stream-timecode"])

    def EventoVisibilidadIten(self, Mensaje):
        """Recive estado de fuente."""
        NombreFuente = Mensaje.datain["item-name"]
        Visibilidad = Mensaje.datain["item-visible"]
        logger.info(f"OBS[{NombreFuente}] {Visibilidad}")
        SalvarValor("data/obs_fuente.json", NombreFuente, Visibilidad)
        self.actualizarDeck()

    def EventoVisibilidadFiltro(self, Mensaje):
        """Recive estado del filtro."""
        NombreFiltro = Mensaje.datain["filterName"]
        NombreFuente = Mensaje.datain["sourceName"]
        Visibilidad = Mensaje.datain["filterEnabled"]
        logger.info(f"OBS[{NombreFiltro}] {Visibilidad}")
        Data = list()
        Data.append(NombreFuente)
        Data.append(NombreFiltro)
        SalvarValor("data/obs_filtro.json", Data, Visibilidad)
        self.actualizarDeck()

    def SalvarFiltroFuente(self, Fuente):
        """Salva el estado de los filtros de una fuente."""
        DataFuente = self.OBS.call(requests.GetSourceFilters(Fuente))

        ListaFiltros = DataFuente.datain["filters"]
        if ListaFiltros is not None:
            for Filtro in ListaFiltros:
                NombreFiltro = Filtro["name"]
                Data = [Fuente, NombreFiltro, "enabled"]

                SalvarValor("data/obs_filtro.json", [Fuente, NombreFiltro], Filtro["enabled"])

                SalvarValor("data/obs_filtro_opciones.json", Data, Filtro["enabled"])

                Data = [Fuente, NombreFiltro, "type"]
                SalvarValor("data/obs_filtro_opciones.json", Data, Filtro["type"])
                self.SalvarFiltroConfiguraciones(Data[:-1], Filtro["settings"])

    def SalvarFiltroConfiguraciones(self, Filtro, lista):
        for elemento in lista:
            Data = Filtro.copy()
            Data.append(elemento)
            SalvarValor("data/obs_filtro_opciones.json", Data, lista[elemento])

    def CambiarEscena(self, opciones):
        """Enviá solicitud de cambiar de Escena."""
        if "escena" in opciones:
            Escena = opciones["escena"]
        else:
            logger.info(f"OBS[Escena no definida]")
            return

        if self.Conectado:
            self.OBS.call(requests.SetCurrentScene(Escena))
            logger.info(f"OBS[Cambiando] {Escena}")
        else:
            logger.warning("OBS[No conectado]")
            self.Notificar("OBS-No-Encontrado")

    def CambiarFuente(self, opciones=False, Fuente=None):
        """Envia solisitud de Cambia el estado de una fuente."""
        if Fuente is None:
            if "fuente" in opciones:
                Fuente = opciones["fuente"]

        if self.Conectado:
            Estado = ObtenerValor("data/obs_fuente.json", Fuente)

            if Estado is not None:
                Estado = not Estado
                logger.info(f"OBS[Fuente] {Fuente}={Estado}")
                self.OBS.call(requests.SetSceneItemProperties(Fuente, visible=Estado))
            else:
                logger.warning(f"No se encontro {Fuente[0]} o {Fuente[1]} en OBS")

        else:
            logger.info("OBS[no Conectado]")
            self.Notificar("OBS No Conectado")

    def CambiarFiltro(self, opciones):
        """Envia solisitud de cambiar estado de filtro."""
        Filtro = None
        Fuente = None
        if "filtro" in opciones:
            Filtro = opciones["filtro"]
        if "fuente" in opciones:
            Fuente = opciones["fuente"]

        if Filtro is None or Fuente is None:
            logger.info("OBS[Falta Atributo]")
            return

        if self.Conectado:
            Estado = ObtenerValor("data/obs_filtro.json", [Fuente, Filtro])
            if Estado is not None:
                Estado = not Estado
                logger.info(f"OBS[Filtro] {Fuente}[{Filtro}]={Estado}")
                self.OBS.call(requests.SetSourceFilterVisibility(Fuente, Filtro, Estado))
        else:
            logger.info("OBS[no Conectado]")
            self.Notificar("OBS No Conectado")

    def CambiarGrabacion(self, opciones=None):
        """Envia solisitud de cambiar estado de Grabacion."""
        if self.Conectado:
            logger.info("Cambiando[Grabacion]")
            self.OBS.call(requests.StartStopRecording())
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS No Conectado")

    def CambiarEnVivo(self, opciones=None):
        """Envia solisitud de cambiar estado del Streaming ."""
        if self.Conectado:
            logger.info("Cambiando estado EnVivo")
            self.OBS.call(requests.StartStopStreaming())
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS No Conectado")

    def CambiarCamaraVirtual(self, opciones=None):
        if self.Conectado:

            logger.info("OBS[Cambiando] CamaraVirtual")
            Solisitud = requests.Baserequests()
            Solisitud.name = "StartStopVirtualCam"
            self.OBS.call(Solisitud)
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def TiempoGrabando(self, opciones=None):
        if self.Conectado:
            consulta = self.OBS.call(requests.GetStreamingStatus())
            if consulta.getRecording():
                tiempo = consulta.getRecTimecode().split(".")[0]
                logger.info(f"Tiempo Grabando: {tiempo}")
                return tiempo
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")
        return "No-Grabando"

    def TiempoEnVivo(self, opciones=None):
        if self.Conectado:
            consulta = self.OBS.call(requests.GetStreamingStatus())
            if consulta.getStreaming():
                tiempo = consulta.getStreamTimecode().split(".")[0]
                logger.info(f"Tiempo Envivo: {tiempo}")
                return tiempo
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-EnVivo")
        return "No-EnVivo"
        pass

    def LimpiarTemporales(self):
        """Limpia los archivos con información temporal de OBS."""
        SalvarArchivo("data/obs.json", dict())
        SalvarArchivo("data/obs_fuente.json", dict())
        SalvarArchivo("data/obs_filtro.json", dict())
        SalvarArchivo("data/obs_filtro_opciones.json", dict())

    def Desconectar(self, opciones=False):
        """Deconectar de OBS websocket."""
        logger.info(f"OBS[Desconectar] - {self.host}")
        if self.Conectado:
            self.OBS.disconnect()
            self.LimpiarTemporales()
        self.Conectado = False
        SalvarValor("data/obs.json", "obs_conectar", False)
        self.actualizarDeck()
        logger.info("Desconeccion correcta")

    def __del__(self):
        """Borrar objeto de Websocket ."""
        self.Desconectar()

    def EventoPrueva(self, Mensaje):
        print(Mensaje)

    def Notificar(self, Mensaje):
        if self.Notificaciones is not None:
            self.Notificaciones(Mensaje, self.alertaOBS)

    def EstadoOBS(self, Opciones):
        conectado = ObtenerValor(self.archivoEstado, "obs_conectar")
        if conectado is None or not conectado:
            self.Notificar("OBS-No-Conectado")
        else:
            self.Notificar("OBS-Conectado")

        grabando = ObtenerValor(self.archivoEstado, "obs_grabar")
        if grabando is None or not grabando:
            self.Notificar("OBS-No-Grabando")
        else:
            self.Notificar("OBS-Grabando")

        enVivo = ObtenerValor(self.archivoEstado, "obs_envivo")
        if enVivo is None or not enVivo:
            self.Notificar("OBS-No-EnVivo")
        else:
            self.Notificar("OBS-EnVivo")

    def Consultas(self):
        # print(dir(requests))
        print()
        print(dir(events))
        print()
