# Librería: https://github.com/Elektordi/obs-websocket-py
# librería temporal: https://github.com/chepecarlos/obs-websocket-py
# Protocolo https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md
import threading
import time
from math import log

from obswebsocket import events, obsws, requests

from elGarrobo.accionesOOP import accionMQTT
from elGarrobo.miLibrerias import (
    ConfigurarLogging,
    ObtenerValor,
    SalvarArchivo,
    SalvarValor,
    leerData,
)

logger = ConfigurarLogging(__name__)


class MiOBS:
    """Concepción con OBS."""

    def __init__(self):
        """Crea confección básica con OBS Websocket."""
        logger.info("OBS[Iniciando]")
        self.archivoEstado = "data/obs/obs"
        """Archivo de estado de OBS."""
        self.audioMonitoriar = list()
        self.dibujar = None
        self.notificaciones: callable = None
        self.procesoTiempo = None
        self.Reiniciar()

    def Reiniciar(self):
        """Reiniciar todo los estado"""
        logger.info("OBS[Reiniciando]")
        self.host = "localhost"
        self.port = 4455
        self.password = None
        self.conectado = False
        self.LimpiarTemporales()
        SalvarValor(self.archivoEstado, "obs_conectar", False)

    def CambiarHost(self, host: int):
        """Cambia el host a conectarse."""
        self.host = host

    def IniciarAcciones(self, listaAcciones):
        """Acciones para controlar OBS"""
        listaAcciones["obs_conectar"] = self.Conectar
        listaAcciones["obs_desconectar"] = self.Desconectar
        listaAcciones["obs_grabar"] = self.CambiarGrabacion
        listaAcciones["obs_pausar"] = self.CambiarPausa
        listaAcciones["obs_envivo"] = self.CambiarEnVivo
        listaAcciones["obs_camara_virtual"] = self.CambiarCamaraVirtual
        listaAcciones["obs_escena"] = self.CambiarEscena
        listaAcciones["obs_fuente"] = self.CambiarFuente
        listaAcciones["obs_filtro"] = self.CambiarFiltro
        listaAcciones["obs_filtro_propiedad"] = self.CambiarFiltroPropiedad
        listaAcciones["obs_estado"] = self.EstadoOBS
        listaAcciones["obs_tiempo_grabando"] = self.TiempoGrabando
        listaAcciones["obs_tiempo_envivo"] = self.TiempoEnVivo

        listaAcciones["obs_grabar_vertical"] = self.cambiarGrabacionVertical
        listaAcciones["obs_envivo_vertical"] = self.cambiarEnVivoVertical
        listaAcciones["obs_escena_vertical"] = self.cambiarEscenaVertical

        # listaAcciones['obs_host'] = self.OBS.Conectar
        # listaAcciones['obs_server'] = self.OBS.Conectar

    def DibujarDeck(self, funcion):
        """Guarda Funcion para refrescar iconos StringDeck."""
        self.dibujar = funcion

    def actualizarDeck(self):
        """Dibuja en StreanDeck si es posible"""
        if self.dibujar is not None:
            self.dibujar()

    def AgregarNotificacion(self, funcion):
        """Agrega función para notificación."""
        self.alertaOBS = leerData("modulos/alerta_obs/mqtt")
        self.notificaciones = funcion

    def Conectar(self, opciones):
        """Se conecta a OBS Websocket y inicializa los eventos."""
        if "servidor" in opciones:
            self.host = opciones["servidor"]
        if "puerto" in opciones:
            self.port = opciones["puerto"]
        if "contrasenna" in opciones:
            self.password = opciones["contrasenna"]

        if self.conectado:
            logger.info("OBS Ya Conectado")
            self.Notificar("OBS-Ya-Conectado")
            return

        modulos = leerData("modulos/modulos")
        monitorAudio = modulos.get("obs_monitor_audio", False)

        if monitorAudio:
            self.audioMonitoriar = leerData("modulos/audio_obs/audio")
            self.audioTopico = leerData("modulos/audio_obs/mqtt")["topic"]

        try:
            if self.password is None:
                self.OBS = obsws(self.host, self.port, on_connect=self.conectarOBS, on_disconnect=self.desconectarOBS)
            else:
                self.OBS = obsws(self.host, self.port, self.password, on_connect=self.conectarOBS, on_disconnect=self.desconectarOBS)
            self.OBS.connect(input_volume_meters=monitorAudio)
        except Exception as error:
            logger.warning(f"OBS[Error] Coneccion {error}")
            self.LimpiarTemporales()
            self.conectado = False
            SalvarValor(self.archivoEstado, "obs_conectar", False)
            self.Notificar("OBS-No-Encontrado")
            return
        self.SalvarEstadoActual()
        # self.AgregarEvento()
        # self.OBS.call(requests.SetHeartbeat(True))
        self.AgregarEvento(self.EventoEscena, events.CurrentProgramSceneChanged)
        self.AgregarEvento(self.EventoGrabando, events.RecordStateChanged)
        self.AgregarEvento(self.EventoEnVivo, events.StreamStateChanged)
        self.AgregarEvento(self.EventoWebCamara, events.VirtualcamStateChanged)
        self.AgregarEvento(self.EventoVisibilidadFuente, events.SceneItemEnableStateChanged)
        self.AgregarEvento(self.EventoVisibilidadFiltro, events.SourceFilterEnableStateChanged)
        self.AgregarEvento(self.EventoCambioFiltro, events.SourceFilterSettingsChanged)
        self.AgregarEvento(self.eventoVendendor, events.VendorEvent)
        self.AgregarEvento(self.eventoExtra, events.CustomEvent)
        self.AgregarEvento(self.EventoSalir, events.ExitStarted)
        self.AgregarEvento(self.eventoVolumen, events.InputVolumeMeters)
        # self.OBS.register(self.on_event, events.StreamStatus)

        # self.AgregarEvento(self.EventoPulsoCorazon, events.Heartbeat)
        self.actualizarDeck()

    def conectarOBS(self, mensaje):
        self.conectado = True
        logger.info(f"OBS[Conectado] {self.host}")
        self.Notificar("OBS-Conectado")

    def desconectarOBS(self, mensaje):
        self.conectado = False
        logger.info("OBS[Desconectado]")
        self.Notificar("OBS-No-Conectado")
        self.LimpiarTemporales()
        self.actualizarDeck()

    def SalvarEstadoActual(self):
        """Salta estado inicial de OBS para StreamDeck."""
        # Todo obtener tiempo de grabacion con self.OBS.call(requests.GetRecordStatus())
        escenaActual = self.OBS.call(requests.GetSceneList()).datain["currentProgramSceneName"]
        estadoGrabando = self.OBS.call(requests.GetRecordStatus()).datain["outputActive"]
        estadoEnVivo = self.OBS.call(requests.GetStreamStatus()).datain["outputActive"]
        estadoPausado = self.OBS.call(requests.GetRecordStatus()).datain["outputPaused"]
        SalvarValor(self.archivoEstado, "obs_conectar", self.conectado)
        SalvarValor(self.archivoEstado, "obs_escena", escenaActual)
        SalvarValor(self.archivoEstado, "obs_grabar", estadoGrabando)
        SalvarValor(self.archivoEstado, "obs_envivo", estadoEnVivo)
        SalvarValor(self.archivoEstado, "obs_pausar", estadoPausado)

        self.procesoTiempo = threading.Thread(target=self.consultaTiempo)
        self.procesoTiempo.start()
        # TODO; parar hilo si obe se desconecta

        self.SalvarFuente()

    def consultaTiempo(self):
        while True:
            if self.conectado:

                try:
                    estadoGracion = self.OBS.call(requests.GetRecordStatus())
                except Exception as error:
                    logger.warning(f"OBS[Error] Tiempo {error}")
                    print(f"Conectado: {self.conectado}")
                    # mi_obs-consultaTiempo[WARNING]: OBS[Error] Tiempo [Errno 32] Broken pipe
                    time.sleep(10)
                    continue

                tiempoGrabando = estadoGracion.datain["outputTimecode"]
                tiempoGrabando = tiempoGrabando.split(".")[0]
                opciones = {"mensaje": tiempoGrabando, "topic": "alsw/tiempo_obs"}
                objetoMQTT = accionMQTT()
                objetoMQTT.configurar(opciones)
                objetoMQTT.ejecutar()
            else:
                pass
            time.sleep(1)
        logger.info("OBS[Consulta Tiempo] - Terminado")

    def SalvarFuente(self):
        HiloFuentes = threading.Thread(target=self.HiloFuenteArchivo)
        HiloFuentes.start()

    def HiloFuenteArchivo(self):
        refrescar = False
        escenaActual = self.OBS.call(requests.GetSceneList()).datain["currentProgramSceneName"]
        data = self.OBS.call(requests.GetSceneItemList(sceneName=escenaActual)).datain
        for fuente in data["sceneItems"]:
            nombreFuente = fuente["sourceName"]
            estadoFuente = fuente["sceneItemEnabled"]
            idFuente = fuente["sceneItemId"]
            estadoFuenteViejo = ObtenerValor(unirPath(self.archivoEstado, "fuente"), nombreFuente)

            if estadoFuente != estadoFuenteViejo:
                SalvarValor(unirPath(self.archivoEstado, "fuente"), nombreFuente, estadoFuente)
                refrescar = True

            SalvarValor(unirPath(self.archivoEstado, "fuente_id"), [escenaActual, idFuente], nombreFuente)
            self.SalvarFiltroFuente(nombreFuente)

        if refrescar:
            self.actualizarDeck()

    def AgregarEvento(self, Funcion, Evento):
        """Registra evento de OBS a una funcion."""
        self.OBS.register(Funcion, Evento)

    def eventoExtra(self, mensaje):
        logger.info(f"OBS[Evento] {mensaje}")

    def EventoEscena(self, mensaje):
        """Recibe nueva escena actual."""
        escenaActual = mensaje.datain["sceneName"]
        SalvarValor(self.archivoEstado, "obs_escena", escenaActual)
        logger.info(f"OBS[Escena] {escenaActual}")
        self.SalvarFuente()
        self.actualizarDeck()

    def EventoGrabando(self, mensaje):
        """Recibe estado de grabación."""
        estadoGrabado = mensaje.datain["outputState"]

        if estadoGrabado == "OBS_WEBSOCKET_OUTPUT_STARTED":
            self.Notificar("OBS-Grabando")
            SalvarValor(self.archivoEstado, "obs_grabar", True)
        elif estadoGrabado == "OBS_WEBSOCKET_OUTPUT_STOPPED":
            self.Notificar("OBS-No-Grabando")
            SalvarValor(self.archivoEstado, "obs_grabar", False)
            SalvarValor(self.archivoEstado, "obs_pausar", False)
        elif estadoGrabado == "OBS_WEBSOCKET_OUTPUT_PAUSED":
            self.Notificar("OBS-Pause-Grabando")
            SalvarValor(self.archivoEstado, "obs_pausar", True)
        elif estadoGrabado == "OBS_WEBSOCKET_OUTPUT_RESUMED":
            self.Notificar("OBS-Re-Grabando")
            SalvarValor(self.archivoEstado, "obs_pausar", False)
        else:
            logger.info(f"OBS[Grabando] Desconocido - {estadoGrabado}")
        self.actualizarDeck()

    def EventoEnVivo(self, mensaje):
        """Recibe estado del Striming."""
        estado = mensaje.datain["outputActive"]
        SalvarValor(self.archivoEstado, "obs_envivo", estado)
        logger.info(f"OBS[EnVivo] - {estado}")
        if estado:
            self.Notificar("OBS-EnVivo")
        else:
            self.Notificar("OBS-No-EnVivo")
        self.actualizarDeck()

    def EventoWebCamara(self, mensaje):
        """Recibe estado del WebCamara"""
        estado = mensaje.datain["outputActive"]
        SalvarValor(self.archivoEstado, "obs_webcamara", estado)
        logger.info(f"OBS[WebCamara] - {estado}")
        if estado:
            self.Notificar("OBS-WebCamara")
        else:
            self.Notificar("OBS-No-WebCamara")
        self.actualizarDeck()

    def EventoSalir(self, mensaje):
        """Recibe desconeccion de OBS websocket."""
        logger.info("OBS[Desconectado]")
        self.Notificar("OBS-No-Conectado")
        try:
            self.Desconectar()
        except Exception as error:
            logger.warning(f"OBS[Error] Salida {error}")
            self.conectado = False
        self.LimpiarTemporales()
        self.actualizarDeck()

    def EventoPulsoCorazon(self, mensaje):
        if mensaje.name == "Heartbeat":
            logger.info("Pulso de OBS")

    def EventoVisibilidadFuente(self, mensaje):
        """Recive estado de fuente."""
        escenaActual = mensaje.datain["sceneName"]
        idFuente = mensaje.datain["sceneItemId"]
        visibilidad = mensaje.datain["sceneItemEnabled"]
        nombreFuente = ObtenerValor(unirPath(self.archivoEstado, "fuente_id"), [escenaActual, idFuente])
        SalvarValor(unirPath(self.archivoEstado, "fuente"), nombreFuente, visibilidad)
        self.actualizarDeck()

    def EventoVisibilidadFiltro(self, mensaje):
        """Recive estado del filtro."""
        # Reparar problema con Filtro
        nombreFiltro = mensaje.datain["filterName"]
        nombreFuente = mensaje.datain["sourceName"]
        visibilidad = mensaje.datain["filterEnabled"]
        logger.info(f"OBS[{nombreFiltro}] {visibilidad}")
        SalvarValor(unirPath(self.archivoEstado, "filtro"), [nombreFuente, nombreFiltro], visibilidad)
        self.actualizarDeck()

    def EventoCambioFiltro(self, mensaje):
        """Recibe cambio de configuracion de filtro."""
        print("Evento Cambio Filtro")
        print(mensaje)

    def SalvarFiltroFuente(self, fuente):
        """Salva el estado de los filtros de una fuente."""
        filtros = self.OBS.call(requests.GetSourceFilterList(sourceName=fuente)).datain["filters"]
        if filtros is None:
            return

        for filtro in filtros:
            nombreFiltro = filtro["filterName"]
            estadoFiltro = filtro["filterEnabled"]
            propiedadesFiltro = filtro.get("filterSettings", {})
            SalvarValor(unirPath(self.archivoEstado, "filtro"), [fuente, nombreFiltro], estadoFiltro)
            for propiedad in propiedadesFiltro:
                SalvarValor(unirPath(self.archivoEstado, "filtro_propiedades"), [fuente, nombreFiltro, propiedad], propiedadesFiltro[propiedad])

    def eventoVendendor(self, mensaje):
        """Recibe mensajes de plugins extras"""
        vendedor = mensaje.datain["vendorName"]
        if vendedor == "aitum-vertical-canvas":
            self.eventoVertical(mensaje)
        else:
            logger.info(f"OBS[Plugin] {vendedor} - {mensaje.datain['eventType']}")

    def eventoVertical(self, mensaje):
        """Recibe mensajes para el plugin de Vertical"""
        tipo = mensaje.datain["eventType"]
        if tipo == "switch_scene":
            escenaActual = mensaje.datain["eventData"]["new_scene"]
            SalvarValor(self.archivoEstado, "obs_escena_vertical", escenaActual)
            logger.info(f"OBS[Escena-Vertical] {escenaActual}")
        elif tipo == "recording_started":
            self.Notificar("obs-grabando-vertival")
            SalvarValor(self.archivoEstado, "obs_grabar_vertical", True)
        elif tipo == "recording_stopping":
            self.Notificar("obs-no-grabando-vertival")
            SalvarValor(self.archivoEstado, "obs_grabar_vertical", False)
        else:
            logger.info(f"OBS[Vertical] No procesar: {tipo}")
        self.actualizarDeck()

    def eventoVolumen(self, mensaje):
        """Recibe mensaje de entradas de Audio"""

        def convertir(nivel):
            return str(round(20 * log(nivel, 10), 1) if nivel > 0 else -200.0)

        canales = mensaje.datain["inputs"]
        for canal in canales:
            for nombres in self.audioMonitoriar:
                if nombres == canal["inputName"]:
                    if len(canal["inputLevelsMul"]) > 0:
                        nivel = canal["inputLevelsMul"][0][1]
                        opciones = {"mensaje": convertir(nivel), "topic": f"{self.audioTopico}/{nombres}"}
                        objetoMQTT = accionMQTT()
                        objetoMQTT.configurar(opciones)
                        objetoMQTT.ejecutar()

    def CambiarEscena(self, opciones):
        """Envía solicitud de cambiar de Escena."""
        escena = opciones.get("escena")

        if escena is None:
            logger.info("OBS[Escena no definida]")
            return

        if self.conectado:
            self.OBS.call(requests.SetCurrentProgramScene(sceneName=escena))  ## problema
            logger.info(f"OBS[Cambiando] {escena}")
        else:
            logger.warning("OBS[No conectado]")
            self.Notificar("OBS-No-Encontrado")

    def CambiarFuente(self, opciones=False, fuente=None):
        """Envía solicitud de Cambia el estado de una fuente."""

        esenaActual = ObtenerValor(self.archivoEstado, "obs_escena")
        if fuente is None:
            if "fuente" in opciones:
                fuente = opciones["fuente"]

        if self.conectado:
            estadoFuente = ObtenerValor(unirPath(self.archivoEstado, "fuente"), fuente)
            print(esenaActual, fuente, estadoFuente)
            idFuente = self.OBS.call(requests.GetSceneItemId(sceneName=esenaActual, sourceName=fuente)).datain["sceneItemId"]
            if estadoFuente is not None:
                estadoFuente = not estadoFuente
                logger.info(f"OBS[Fuente] {esenaActual}-{fuente}={estadoFuente}")
                self.OBS.call(requests.SetSceneItemEnabled(sceneName=esenaActual, sceneItemId=idFuente, sceneItemEnabled=estadoFuente))
            else:
                logger.warning(f"No se encontro {fuente[0]} o {fuente[1]} en OBS")

        else:
            logger.info("OBS[no Conectado]")
            self.Notificar("OBS-No-Conectado")

    def CambiarFiltro(self, opciones):
        """Envía solicitud de cambiar estado de filtro."""
        filtro = opciones.get("filtro")
        fuente = opciones.get("fuente")
        estado = opciones.get("estado")

        if fuente is None or filtro is None:
            logger.info("OBS[Falta Atributo]")
            return

        if self.conectado:
            if estado is None:
                estado = ObtenerValor(unirPath(self.archivoEstado, "filtro"), [fuente, filtro])
                if estado is not None:
                    estado = not estado

            if estado is not None:
                logger.info(f"OBS[Filtro] {fuente}[{filtro}]={estado}")
                self.OBS.call(requests.SetSourceFilterEnabled(sourceName=fuente, filterName=filtro, filterEnabled=estado))
        else:
            logger.info("OBS[no Conectado]")
            self.Notificar("OBS-No-Conectado")

    def CambiarFiltroPropiedad(self, opciones):
        """Envía solicitud de cambiar propiedades de un filtro."""
        filtro = opciones.get("filtro")
        fuente = opciones.get("fuente")
        agregar = opciones.get("agregar", False)
        propiedad = opciones.get("propiedad")
        valor = opciones.get("valor")

        self.SalvarFiltroFuente(fuente)

        PropiedadesAnteriores = ObtenerValor(unirPath(self.archivoEstado, "filtro_propiedades"), [fuente, filtro])

        if fuente is None or filtro is None or propiedad is None or valor is None:
            logger.info("OBS[Falta Atributo]")
            return

        if PropiedadesAnteriores is not None and agregar:
            for llaveAnterior, valorAnterior in PropiedadesAnteriores.items():
                if llaveAnterior == propiedad:
                    valor = valor + valorAnterior
                    logger.info(f"OBS[Filtro] agregando {valorAnterior} + {valor - valorAnterior} = {valor}")

        if self.conectado:
            logger.info(f"OBS[Filtro Asignar] {fuente}[{filtro}-{propiedad}]={valor}")
            self.OBS.call(requests.SetSourceFilterSettings(sourceName=fuente, filterName=filtro, filterSettings={propiedad: valor}))
            self.SalvarFiltroFuente(fuente)
        else:
            logger.info("OBS[no Conectado]")
            self.Notificar("OBS-No-Conectado")

    def CambiarGrabacion(self, opciones=None):
        """Envia solisitud de cambiar estado de Grabacion."""
        if self.conectado:
            logger.info("Cambiando[Grabacion]")
            self.OBS.call(requests.ToggleRecord())
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def CambiarPausa(self, opciones=None):
        """Envía solisitud de cambiar estado de Pausa Grabacion."""
        if self.conectado:
            logger.info("Cambiando[Pausa]")
            self.OBS.call(requests.ToggleRecordPause())
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def CambiarEnVivo(self, opciones=None):
        """Envia solisitud de cambiar estado del Streaming ."""
        if self.conectado:
            logger.info("Cambiando[EnVivo]")
            self.OBS.call(requests.ToggleStream())
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def CambiarCamaraVirtual(self, opciones=None):
        """Envia solisitud de cambio estado Camara Virtual"""
        if self.conectado:
            self.OBS.call(requests.ToggleVirtualCam())
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def cambiarGrabacionVertical(self, opciones=None):
        """Envia solisitud de cambiar estado de Grabacion en plugin Vertical."""
        if self.conectado:
            logger.info("Cambiando[Grabacion-Vertical]")
            self.OBS.call(requests.CallVendorRequest(vendorName="aitum-vertical-canvas", requestType="toggle_recording"))
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def cambiarEnVivoVertical(self, opciones=None):
        """Envia solisitud de cambiar estado del Streaming ."""
        if self.conectado:
            logger.info("Cambiando[EnVivo-Vertical]")
            self.OBS.call(requests.CallVendorRequest(vendorName="aitum-vertical-canvas", requestType="toggle_streaming"))
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def cambiarEscenaVertical(self, opciones=None):
        """Enviá solicitud de cambiar de Escena en plugin Vertical."""
        escena = opciones.get("escena")

        if escena is None:
            logger.info("OBS[Escena no definida]")
            return

        if self.conectado:
            mensaje = {"scene": escena}
            self.OBS.call(requests.CallVendorRequest(vendorName="aitum-vertical-canvas", requestType="switch_scene", requestData=mensaje))
            logger.info(f"OBS[Cambiando-Vertical] {escena}")
        else:
            logger.warning("OBS[No conectado]")
            self.Notificar("OBS-No-Encontrado")

    def TiempoGrabando(self, opciones=None):
        if self.conectado:
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
        if self.conectado:
            consulta = self.OBS.call(requests.GetStreamingStatus())
            if consulta.getStreaming():
                tiempo = consulta.getStreamTimecode().split(".")[0]
                logger.info(f"Tiempo Envivo: {tiempo}")
                return tiempo
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-EnVivo")
        return "No-EnVivo"

    def LimpiarTemporales(self):
        """Limpia los archivos con información temporal de OBS."""
        SalvarArchivo(self.archivoEstado, dict())
        SalvarArchivo(unirPath(self.archivoEstado, "fuente"), dict())
        SalvarArchivo(unirPath(self.archivoEstado, "filtro"), dict())
        SalvarArchivo(unirPath(self.archivoEstado, "filtro_propiedades"), dict())
        SalvarArchivo(unirPath(self.archivoEstado, "filtro_opciones"), dict())
        SalvarArchivo(unirPath(self.archivoEstado, "fuente_id"), dict())

    def Desconectar(self, opciones=False):
        """Deconectar de OBS websocket."""
        logger.info(f"OBS[Desconectar] - {self.host}")
        if self.conectado:
            self.OBS.disconnect()
            self.LimpiarTemporales()
        self.conectado = False
        SalvarValor(self.archivoEstado, "obs_conectar", False)
        self.actualizarDeck()
        logger.info("Desconeccion correcta")

    def __del__(self):
        """Borrar objeto de Websocket ."""
        self.Desconectar()

    def EventoPrueva(self, Mensaje):
        logger.info("Evento pruva OBS", Mensaje)

    def Notificar(self, Mensaje):
        if self.notificaciones is not None:
            self.notificaciones(Mensaje, self.alertaOBS)

    def EstadoOBS(self, opciones):
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

        webCamara = ObtenerValor(self.archivoEstado, "obs_webcamara")
        if webCamara is None or not webCamara:
            self.Notificar("OBS-No-WebCamara")
        else:
            self.Notificar("OBS-WebCamara")

    def Consultas(self):
        # print(dir(requests))
        print()
        print(dir(events))
        print()
        # Solisitud = requests.Baserequests()
        # Solisitud.name = "StartStopVirtualCam"
        # self.OBS.call(Solisitud)


def unirPath(ruta1, ruta2):
    return f"{ruta1}_{ruta2}"
