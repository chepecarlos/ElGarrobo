# Librería:https://github.com/aatikturk/obsws-python
# Protocolo https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

import logging
import threading
import time
from math import log

import obsws_python as obs
from obsws_python import error as OBSerror

from elGarrobo.accionesOOP import accion, accionMQTT
from elGarrobo.miLibrerias import (
    ConfigurarLogging,
    ObtenerValor,
    SalvarArchivo,
    SalvarValor,
    leerData,
)

logger = ConfigurarLogging(__name__, logging.DEBUG)


class MiOBS:
    """Concepción con OBS WebSocket."""

    clienteConsultas: obs.ReqClient = None
    "Cliente para mandar información a OBS WebSocket"
    clienteEvento: obs.EventClient = None
    "Cliente para recibir información de OBS WebSocket"
    conectado: bool = False
    "Esta conectado con OBS WebSocket"

    servidor: str
    "Servidor a conectarse con obs"
    puerto: int
    "Puerto a usar para conectarse con obs"
    password: str
    "Contraseña para conectar con obs"

    escenaActual: str
    "Escena actual de OBS"
    grabando: bool
    "Esta grabando en OBS"
    enVivo: bool
    "Esta trasmitiendo en OBS"
    audioMonitoriar: list[str]
    "audio a monitoria y enviar por mqtt"
    audioTopico: str
    "Topic base para enviar audio por mqtt"

    archivoEstado: str = "data/obs/obs"

    consultaCliente: bool
    "se esta haciendo una consulta fuente"

    notificaciones: callable
    "Función para notificaciones a MQTT"

    def __init__(self) -> None:
        """Crea confección básica con OBS Websocket."""
        logger.info("OBS[Iniciando]")
        """Archivo de estado de OBS."""
        self.audioMonitoriar = list()
        self.dibujar = None
        self.notificaciones: callable = None
        self.conectado = False
        self.procesoTiempo = None
        self.consultaCliente = False

        self.Reiniciar()

    def conectar(self, opciones: dict) -> bool:
        """Se conecta a OBS Websocket y inicializa los eventos.

        Args:
            opciones

        Returns:
            bool: True si se conecto, False si no
        """

        if self.conectado:
            logger.info("OBS[Ya Conectado]")
            self.Notificar("OBS-Ya-Conectado")
            return False

        self.servidor: str = opciones.get("servidor", "localhost")
        self.puerto: int = int(opciones.get("puerto", 4455))
        self.password: str | None = opciones.get("password", None)

        modulos = leerData("modulos")
        monitorAudio = modulos.get("obs_monitor_audio", False)

        if monitorAudio:
            self.audioMonitoriar = leerData("modulos/audio_obs/audio")
            self.audioTopico = leerData("modulos/audio_obs/mqtt").get("topic")

        logger.info("OBS[Conectando]")

        try:
            self.OBS = None

            parametros: dict = {
                "host": self.servidor,
                "port": self.puerto,
            }

            if self.password:
                parametros["password"] = self.password

            self.clienteConsultas = obs.ReqClient(**parametros)

            parametros["subs"] = obs.Subs.LOW_VOLUME | obs.Subs.INPUTVOLUMEMETERS
            self.clienteEvento = obs.EventClient(**parametros)

        except ConnectionRefusedError:
            logger.info("No se encuentra OBS")
            self.Notificar("OBS-No-Encontrado")
            self.clienteConsultas = None
            self.clienteEvento = None
            self.LimpiarTemporales()
            SalvarValor(self.archivoEstado, "obs_conectar", False)
            self.conectado = False
            return False
        except Exception as error:
            logger.exception(f"OBS[Error] Colección {error}")
            self.clienteConsultas = None
            self.clienteEvento = None
            self.conectado = False
            self.LimpiarTemporales()
            SalvarValor(self.archivoEstado, "obs_conectar", False)
            self.Notificar("OBS-No-Encontrado")
            return False

        inicio = time.time()
        while self.clienteConsultas is None:
            if time.time() - inicio > 5:
                logger.warning("OBS: Timeout esperando ReqClient.")
            time.sleep(0.1)

        logger.info("OBS[Conectado]")
        self.Notificar("OBS-Conectado")

        self.conectado = True

        self.configurarEventos()

        self.salvarEstadoActual()
        time.sleep(0.5)
        self.empezarConsultaTiempo()

        # Evento actual
        # self.AgregarEvento(self.EventoCambioFiltro, events.SourceFilterSettingsChanged)

        # self.OBS.register(self.on_event, events.StreamStatus)

        return True

    def configurarEventos(self):

        self.clienteEvento.callback.register(
            [
                self.on_current_program_scene_changed,
                self.on_scene_item_enable_state_changed,
                self.on_record_state_changed,
                self.on_input_volume_meters,
                self.on_virtualcam_state_changed,
                self.on_stream_state_changed,
                self.on_vendor_event,
                self.on_source_filter_enable_state_changed,
                #         # self.on_scene_created,
                # self.on_input_mute_state_changed,
                self.on_exit_started,
            ]
        )
        logger.info(f"Eventos registrados en OBS:")
        for evento in self.clienteEvento.callback.get():
            logger.info(f" - {evento}")

    def IniciarAcciones(self, listaAcciones: dict) -> None:
        """Acciones para controlar OBS

        Args:
            listaAcciones (dict): Diccionario de acciones para agregar
        """
        listaAcciones["obs_conectar"] = self.conectar
        listaAcciones["obs_desconectar"] = self.desconectar
        listaAcciones["obs_grabar"] = self.cambiarGrabacion
        listaAcciones["obs_pausar"] = self.cambiarPausa
        listaAcciones["obs_envivo"] = self.cambiarEnVivo
        listaAcciones["obs_escena"] = self.cambiarEscena
        listaAcciones["obs_fuente"] = self.cambiarFuente
        listaAcciones["obs_camara_virtual"] = self.cambiarCamaraVirtual
        listaAcciones["obs_filtro"] = self.cambiarFiltro
        listaAcciones["obs_filtro_propiedad"] = self.CambiarFiltroPropiedad
        # Lista de acciones verticales
        listaAcciones["obs_grabar_vertical"] = self.cambiarGrabacionVertical
        listaAcciones["obs_envivo_vertical"] = self.cambiarEnVivoVertical
        listaAcciones["obs_escena_vertical"] = self.cambiarEscenaVertical
        # listaAcciones["obs_estado"] = self.EstadoOBS
        # listaAcciones["obs_tiempo_grabando"] = self.TiempoGrabando
        # listaAcciones["obs_tiempo_envivo"] = self.TiempoEnVivo

        # listaAcciones['obs_host'] = self.OBS.Conectar
        # listaAcciones['obs_server'] = self.OBS.Conectar

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

    def DibujarDeck(self, funcion):
        """Guarda Funcion para refrescar iconos StringDeck."""
        self.dibujar = funcion

    def actualizarDeck(self):
        """Dibuja en StreanDeck si es posible"""
        if self.dibujar is not None:
            self.dibujar()

    def AgregarNotificacion(self, funcion: callable):
        """Agrega función para notificación."""
        self.alertaOBS = leerData("modulos/alerta_obs/mqtt")
        self.notificaciones = funcion

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

    def salvarEstadoActual(self):
        """Salta estado inicial de OBS para StreamDeck."""

        if not self.conectado:
            logger.warning("No conectado SalvarEstadoActual")
            return

        escenaActual = self.clienteConsultas.get_scene_list()

        if escenaActual is None:
            self.escenaActual = "Desconocido"
        else:
            self.escenaActual = escenaActual.current_program_scene_name

        grabando = self.clienteConsultas.get_record_status()
        self.grabando = grabando.output_active
        self.pausado = grabando.output_paused

        enVivo = self.clienteConsultas.get_stream_status()
        self.enVivo = enVivo.output_active

        SalvarValor(self.archivoEstado, "obs_conectar", self.conectado)
        SalvarValor(self.archivoEstado, "obs_escena", self.escenaActual)
        SalvarValor(self.archivoEstado, "obs_grabar", self.grabando)
        SalvarValor(self.archivoEstado, "obs_pausar", self.pausado)
        SalvarValor(self.archivoEstado, "obs_envivo", self.enVivo)

        self.salvarFuente()

        #
        # # TODO; parar hilo si obe se desconecta

    def empezarConsultaTiempo(self):
        self.procesoTiempo = threading.Thread(target=self.consultaTiempo, name="ElGarroboOBS-consultaTiempo")
        self.procesoTiempo.start()

    def consultaTiempo(self):
        while True:
            if not self.conectado:
                break

            if self.grabando and not self.consultaCliente:

                self.consultaCliente = True
                try:
                    respuestaEstado = self.clienteConsultas.get_record_status()

                except Exception as error:
                    logger.exception(f"OBS[Error] Tiempo {error}")
                    # TODO: Error mi_obs-consultaTiempo[WARNING]: OBS[Error] Tiempo [Errno 32] Broken pipe ?
                    self.consultaCliente = False
                    time.sleep(10)
                    continue
                self.consultaCliente = False

                if respuestaEstado is None or not hasattr(respuestaEstado, "output_timecode"):
                    print("No hay tiempo de grabación")
                    continue

                tiempoGrabando: str = respuestaEstado.output_timecode
                tiempoGrabando = tiempoGrabando.split(".")[0]

            else:
                tiempoGrabando = "00:00:00"

            opciones = {"mensaje": tiempoGrabando, "topic": "alsw/tiempo_obs"}
            objetoMQTT: accion = accionMQTT()
            objetoMQTT.configurar(opciones)
            objetoMQTT.ejecutar()

            time.sleep(1)
        logger.info("OBS[Consulta Tiempo] - Terminado")

    def salvarFuente(self):
        # print("Hilo cargado Fuente " + str(threading.active_count()))
        if self.consultaCliente:
            logger.warning("Ya se esta salvando fuente")
            return

        self.consultaCliente = True
        try:
            HiloFuentes = threading.Thread(target=self.hiloSalvarFuentes, name="ElGarroboOBS-salvarFuentes")
            HiloFuentes.start()
        except Exception as error:
            logger.exception(f"OBS[Error] Hilo Fuente {error}")
        self.consultaCliente = False

    def hiloSalvarFuentes(self):
        """Salva la información de las fuentes"""

        refrescar = False

        if not self.conectado:
            return

        escenaActual: str = self.clienteConsultas.get_scene_list()
        self.escenaActual = escenaActual.current_program_scene_name

        data = self.clienteConsultas.get_scene_item_list(self.escenaActual)
        if data is None:
            return

        for fuente in data.scene_items:
            idFuente = fuente.get("sceneItemId")
            nombreFuente = fuente.get("sourceName")
            estadoFuente = fuente.get("sceneItemEnabled")
            tipoFuente = fuente.get("sourceType")
            estadoFuenteViejo = ObtenerValor(unirPath(self.archivoEstado, "fuente"), nombreFuente)

            if estadoFuente != estadoFuenteViejo:
                SalvarValor(unirPath(self.archivoEstado, "fuente"), nombreFuente, estadoFuente)
                refrescar = True

            SalvarValor(unirPath(self.archivoEstado, "fuente_id"), [self.escenaActual, idFuente], nombreFuente)
            self.SalvarFiltroFuente(nombreFuente)

        if refrescar:
            self.actualizarDeck()

    def AgregarEvento(self, Funcion, Evento):
        """Registra evento de OBS a una funcion."""
        self.OBS.register(Funcion, Evento)

    def eventoExtra(self, mensaje):
        logger.info(f"OBS[Evento] {mensaje}")

    def on_current_program_scene_changed(self, mensaje):
        """Recibe nueva escena actual."""
        self.escenaActual = mensaje.scene_name
        SalvarValor(self.archivoEstado, "obs_escena", self.escenaActual)
        logger.info(f"OBS[Escena] {self.escenaActual}")
        self.salvarFuente()
        # self.salvarEstadoActual()
        self.actualizarDeck()

    def on_record_state_changed(self, mensaje):
        """Recibe estado de grabación."""

        estadoGrabado = mensaje.output_state

        if estadoGrabado == "OBS_WEBSOCKET_OUTPUT_STARTED" or estadoGrabado == "OBS_WEBSOCKET_OUTPUT_STARTING":
            self.Notificar("OBS-Grabando")
            self.grabando = True
        elif estadoGrabado == "OBS_WEBSOCKET_OUTPUT_STOPPED" or estadoGrabado == "OBS_WEBSOCKET_OUTPUT_STOPPING":
            self.Notificar("OBS-No-Grabando")
            self.grabando = False
            self.pausado = False
        elif estadoGrabado == "OBS_WEBSOCKET_OUTPUT_PAUSED":
            self.Notificar("OBS-Pause-Grabando")
            self.pausado = True
        elif estadoGrabado == "OBS_WEBSOCKET_OUTPUT_RESUMED":
            self.Notificar("OBS-Re-Grabando")
            self.pausado = False
        else:
            logger.info(f"OBS[Grabando] Desconocido - {estadoGrabado}")
            return

        SalvarValor(self.archivoEstado, "obs_grabar", self.grabando)
        SalvarValor(self.archivoEstado, "obs_pausar", self.pausado)
        self.actualizarDeck()

    def on_stream_state_changed(self, mensaje):
        """Recibe estado del Striming."""
        estado = mensaje.output_active
        SalvarValor(self.archivoEstado, "obs_envivo", estado)
        logger.info(f"OBS[EnVivo] - {estado}")
        if estado:
            self.Notificar("OBS-EnVivo")
            self.envivo = True
        else:
            self.Notificar("OBS-No-EnVivo")
            self.envivo = False
        self.actualizarDeck()

    def on_virtualcam_state_changed(self, mensaje):
        """Recibe estado del WebCamara"""
        estado = mensaje.output_active
        SalvarValor(self.archivoEstado, "obs_camara_virtual", estado)
        logger.info(f"OBS[WebCamara] - {estado}")
        if estado:
            self.Notificar("OBS-WebCamara")
        else:
            self.Notificar("OBS-No-WebCamara")
        self.actualizarDeck()

    def on_scene_item_enable_state_changed(self, mensaje):
        """Recibe estado de fuente."""

        escenaActual = mensaje.scene_name
        idFuente = mensaje.scene_item_id
        visibilidad = mensaje.scene_item_enabled
        archivoFuentesID = unirPath(self.archivoEstado, "fuente_id")
        nombreFuente = ObtenerValor(archivoFuentesID, [escenaActual, idFuente], depuracion=True)
        SalvarValor(unirPath(self.archivoEstado, "fuente"), nombreFuente, visibilidad)
        self.actualizarDeck()

    def on_source_filter_enable_state_changed(self, mensaje):
        """Recive estado del filtro."""
        nombreFiltro = mensaje.filter_name
        nombreFuente = mensaje.source_name
        visibilidad = mensaje.filter_enabled
        logger.info(f"OBS[{nombreFiltro}-{nombreFuente}] {visibilidad}")
        archivoFiltro: str = unirPath(self.archivoEstado, "filtro")
        SalvarValor(archivoFiltro, [nombreFuente, nombreFiltro], visibilidad, depuracion=True)
        self.actualizarDeck()

    def EventoCambioFiltro(self, mensaje):
        """Recibe cambio de configuracion de filtro."""
        print("Evento Cambio Filtro")
        print(mensaje)

    def SalvarFiltroFuente(self, fuente: str):
        """Salva el estado de los filtros de una fuente.

        Args:
            fuente (str): Nombre de la fuente
        """

        consultaFiltros = self.clienteConsultas.get_source_filter_list(fuente)

        if consultaFiltros is None:
            print("No hay filtros")
            return

        filtros = consultaFiltros.filters

        if filtros is None:
            return

        dataPropiedades = leerData(unirPath(self.archivoEstado, "filtro_propiedades"))
        if dataPropiedades is not None:
            dataFuenteAnterior = dataPropiedades.get(fuente)

        for filtro in filtros:
            nombreFiltro = filtro.get("filterName")
            estadoFiltro = filtro.get("filterEnabled")
            propiedadesFiltro = filtro.get("filterSettings", {})

            SalvarValor(unirPath(self.archivoEstado, "filtro"), [fuente, nombreFiltro], estadoFiltro)
            for propiedad in propiedadesFiltro:

                if dataFuenteAnterior is not None:
                    dataFiltroAnterior = dataFuenteAnterior.get(nombreFiltro)
                    if dataFiltroAnterior is not None:
                        valorPropiedadAnterior = dataFiltroAnterior.get(propiedad)
                        if valorPropiedadAnterior is not None and valorPropiedadAnterior == propiedadesFiltro[propiedad]:
                            continue

                SalvarValor(unirPath(self.archivoEstado, "filtro_propiedades"), [fuente, nombreFiltro, propiedad], propiedadesFiltro[propiedad])

    def on_vendor_event(self, mensaje):
        """Recibe mensajes de plugins extras"""
        vendedor = mensaje.vendor_name
        if vendedor == "aitum-vertical-canvas":
            self.eventoVertical(mensaje)
        else:
            logger.warning(f"OBS[Plugin Desconocido] {vendedor} - {mensaje.event_type}")

    def eventoVertical(self, mensaje):
        """Recibe mensajes para el plugin de Vertical"""
        tipo = mensaje.event_type
        if tipo == "switch_scene":
            dataEvento = mensaje.event_data
            escenaActual = dataEvento.get("new_scene")
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

    def on_input_volume_meters(self, mensaje):
        """Recibe mensaje de entradas de Audio"""

        def convertir(nivel):
            return str(round(20 * log(nivel, 10), 1) if nivel > 0 else -200.0)

        canales = mensaje.inputs

        for canal in canales:
            nombre = canal.get("inputName")
            if nombre in self.audioMonitoriar:
                if len(canal.get("inputLevelsMul")) > 0:
                    nivel = canal.get("inputLevelsMul")[0][1]
                    opciones = {"mensaje": convertir(nivel), "topic": f"{self.audioTopico}/{nombre}"}
                    objetoMQTT = accionMQTT()
                    objetoMQTT.configurar(opciones)
                    objetoMQTT.ejecutar()

    def cambiarEscena(self, opciones):
        """Envía solicitud de cambiar de Escena."""
        escena: str = opciones.get("escena")

        if escena is None:
            logger.info("OBS[Escena no definida]")
            return

        if not self.conectado:
            logger.warning("OBS[No conectado]")
            self.Notificar("OBS-No-Encontrado")
            return

        try:
            self.clienteConsultas.set_current_program_scene(escena)
        except OBSerror.OBSSDKRequestError as e:
            print(f"El error es {e}")
            print(e.req_name, e.code)
            self.Notificar(f"OBS[No existe] {escena}")

        logger.info(f"OBS[Cambiando] {escena}")

    def cambiarFuente(self, opciones: dict):
        """Envía solicitud de Cambia el estado de una fuente."""

        fuente: str = opciones.get("fuente")

        if fuente is None:
            logger.warning("OBS[Falta Fuente]")
            return

        if not self.conectado:
            logger.warning("OBS[No conectado]")
            self.Notificar("OBS-No-Encontrado")
            return

        # TODO: confirmar que exista fuente

        respuestaConsulta = self.clienteConsultas.get_scene_item_id(self.escenaActual, fuente)

        if respuestaConsulta is None:
            logger.warning(f"OBS[No existe] {fuente}")
            self.Notificar(f"OBS[No existe] {fuente}")
            return
        idFuente: int = respuestaConsulta.scene_item_id

        respuestaConsulta: bool = self.clienteConsultas.get_scene_item_enabled(self.escenaActual, idFuente)
        estadoEscena = respuestaConsulta.scene_item_enabled

        logger.info(f"OBS[Cambiando Fuente] {fuente}[{idFuente}] {not estadoEscena}")

        self.clienteConsultas.set_scene_item_enabled(self.escenaActual, idFuente, not estadoEscena)

    def cambiarFiltro(self, opciones):
        """Envía solicitud de cambiar estado de filtro."""
        fuente: str = opciones.get("fuente")
        filtro: str = opciones.get("filtro")
        estado: bool | None = opciones.get("estado")

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
                self.clienteConsultas.set_source_filter_enabled(fuente, filtro, estado)
        else:
            logger.info("OBS[no Conectado]")
            self.Notificar("OBS-No-Conectado")

    def CambiarFiltroPropiedad(self, opciones):
        """Envía solicitud de cambiar propiedades de un filtro."""
        if not self.conectado:
            logger.info("OBS[no Conectado]")
            self.Notificar("OBS-No-Conectado")
            return

        filtro: str = opciones.get("filtro")
        fuente: str = opciones.get("fuente")
        agregar: bool = opciones.get("agregar", False)

        propiedad: str = opciones.get("propiedad")
        valor: str = opciones.get("valor")

        PropiedadesAnteriores = ObtenerValor(unirPath(self.archivoEstado, "filtro_propiedades"), [fuente, filtro])

        if fuente is None or filtro is None or propiedad is None or valor is None:
            logger.info("OBS[Falta Atributo]")
            return

        if PropiedadesAnteriores is not None and agregar:
            for llaveAnterior, valorAnterior in PropiedadesAnteriores.items():
                if llaveAnterior == propiedad:
                    valor = valor + valorAnterior
                    logger.info(f"OBS[Filtro] agregando {valorAnterior} + {valor - valorAnterior} = {valor}")

        agregarTexto = " Agregar" if agregar else ""
        logger.info(f"OBS[Filtro Asignar] {fuente}[{filtro}-{propiedad}]={valor}{agregarTexto}")
        self.clienteConsultas.set_source_filter_settings(
            source_name=fuente,
            filter_name=filtro,
            settings={propiedad: valor},
            overlay=agregar,
        )
        self.SalvarFiltroFuente(fuente)

    def cambiarGrabacion(self, opciones: dict = None):
        """Envía solicitud de cambiar estado de Grabación."""
        if self.conectado:
            logger.info("Cambiando[Grabación]")
            try:
                self.clienteConsultas.toggle_record()
            except KeyError as e:
                logger.error(f"OBS[Error] {e}")
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def cambiarPausa(self, opciones=None):
        """Envía solicitud de cambiar estado de Pausa Grabación."""
        if self.conectado:
            logger.info("Cambiando[Pausa]")
            self.clienteConsultas.toggle_record_pause()
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def cambiarEnVivo(self, opciones=None):
        """Envía solicitud de cambiar estado del Streaming ."""
        if self.conectado:
            logger.info("Cambiando[EnVivo]")
            self.clienteConsultas.toggle_stream()
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def cambiarCamaraVirtual(self, opciones: dict = None):
        """Envía solicitud de cambio estado Cámara Virtual"""
        if self.conectado:
            try:
                self.clienteConsultas.toggle_virtual_cam()
            except KeyError as e:
                logger.error(f"OBS[Error] {e}")
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def cambiarGrabacionVertical(self, opciones=None):
        """Envía solicitud de cambiar estado de Grabación en plugin Vertical."""
        if self.conectado:
            logger.info("Cambiando[Grabación-Vertical]")
            try:
                self.clienteConsultas.call_vendor_request("aitum-vertical-canvas", "toggle_recording")
            except KeyError as e:
                if str(e) == "'requestStatus'":
                    return
                logger.error(f"OBS[Error] {e}")
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def cambiarEnVivoVertical(self, opciones=None):
        """Envía solicitud de cambiar estado del Streaming ."""
        if self.conectado:
            logger.info("Cambiando[EnVivo-Vertical]")
            self.clienteConsultas.call_vendor_request("aitum-vertical-canvas", "toggle_streaming")
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")

    def cambiarEscenaVertical(self, opciones=None):
        """Envía solicitud de cambiar de Escena en plugin Vertical."""
        escena = opciones.get("escena")

        if escena is None:
            logger.info("OBS[Escena no definida]")
            return

        if self.conectado:
            mensaje = {"scene": escena}

            try:
                self.clienteConsultas.call_vendor_request("aitum-vertical-canvas", "switch_scene", mensaje)
            except KeyError as e:
                # Captura el error específico de 'requestStatus'
                logger.error(f"OBS[Error-Vertical] La solicitud falló o hay una incompatibilidad de protocolo. Error: {e}")

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
        SalvarArchivo(unirPath(self.archivoEstado, "fuente_id"), dict())

    def desconectar(self, opciones=False):
        """Deconectar de OBS websocket."""
        logger.info(f"OBS[Desconectando] - {self.host}")
        self.Notificar("OBS-No-Conectado")
        # self._cola_consultas.put(None)
        if not self.conectado:
            return
        self.clienteConsultas.disconnect()
        self.clienteEvento.disconnect()
        self.LimpiarTemporales()
        self.conectado = False
        SalvarValor(self.archivoEstado, "obs_conectar", False)
        self.actualizarDeck()
        logger.info("OBS[Desconectado]")

    def on_exit_started(self, mensaje):
        """Recibe desconeccion de OBS websocket."""
        logger.info("OBS[Desconectado]")
        self.Notificar("OBS-No-Conectado")
        self.conectado = False
        # try:
        #     self.clienteConsultas.des
        #     self.desconectar()
        # except Exception as error:
        #     logger.warning(f"OBS[Error] Salida {error}")
        # self.conectado = False
        self.LimpiarTemporales()
        self.actualizarDeck()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.conectado:
            self.clienteConsultas.disconnect()
            self.clienteEvento.disconnect()

    def __del__(self):
        """Borrar objeto de Websocket ."""
        if self.conectado:
            self.clienteConsultas.disconnect()
            self.clienteEvento.disconnect()

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


def unirPath(ruta1, ruta2):
    return f"{ruta1}_{ruta2}"
