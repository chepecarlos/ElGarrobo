# Librería:https://github.com/aatikturk/obsws-python
# Protocolo https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

import logging
import threading
import time
from collections.abc import Callable
from math import log
from typing import Any

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
from elGarrobo.modulos.modulo import modulo

from .accionesOBS import accionesOBS

logger = ConfigurarLogging(__name__)


class moduloOBS(modulo):
    """Concepción con OBS WebSocket."""

    nombre = "OBS"
    modulo = "obs"
    descripcion = "Control de OBS por WebSocket"
    acciones = accionesOBS

    clienteConsultas: obs.ReqClient | None = None
    "Cliente para mandar información a OBS WebSocket"
    clienteEvento: obs.EventClient | None = None
    "Cliente para recibir información de OBS WebSocket"
    conectado: bool = False
    "Esta conectado con OBS WebSocket"

    servidor: str
    "Servidor a conectarse con obs"
    puerto: int
    "Puerto a usar para conectarse con obs"
    password: str | None
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

    notificaciones: Callable[[str, Any], None] | None
    "Función para notificaciones a MQTT"

    def __init__(self, dataModulo: dict | None = None) -> None:
        """Crea confección básica con OBS Websocket."""
        logger.info("OBS[Iniciando]")
        """Archivo de estado de OBS."""
        self.audioMonitoriar = list()
        self.dibujar = None
        self.notificaciones = None
        self.conectado = False
        self.procesoTiempo = None
        self.consultaCliente = False
        self.grabandoVertical = False
        self.tiempoInicioVertical: float | None = None
        self.host = "localhost"
        self.port = 4455
        self.password = None

    def ejecutar(self):
        """Limpia el estado guardado al activar el módulo"""
        self.Reiniciar()

    def conectar(self, servidor: str = "localhost", puerto: int = 4455, password: str | None = None) -> bool:
        """Se conecta a OBS Websocket y inicializa los eventos.

        Returns:
            bool: True si se conecto, False si no
        """

        if self.conectado:
            logger.info("OBS[Ya Conectado]")
            self.Notificar("OBS-Ya-Conectado")
            return False

        self.servidor = servidor
        self.puerto = int(puerto)
        self.password = password

        modulos = leerData("modulos") or {}
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
        if self.clienteEvento is None:
            logger.warning("OBS[Eventos] Cliente de eventos no disponible")
            return

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
        logger.info("Eventos registrados en OBS:")
        for evento in self.clienteEvento.callback.get():
            logger.info(f" - {evento}")

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

    def AgregarNotificacion(self, función: Callable[[str, Any], None]):
        """Agrega función para notificación."""
        self.alertaOBS = leerData("modulos/alerta_obs/mqtt")
        self.notificaciones = función

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

            elif self.grabandoVertical and self.tiempoInicioVertical is not None:

                segundos = int(time.time() - self.tiempoInicioVertical)
                tiempoGrabando = f"{segundos // 3600:02d}:{(segundos % 3600) // 60:02d}:{segundos % 60:02d}"

            else:
                tiempoGrabando = "00:00:00"

            # opcionesVertical = {"mensaje": tiempoVertical, "topic": "alsw/tiempo_obs_vertical"}
            # TODO: separar tiempo de grabación para vertical y normal
            opcionesVertical = {"mensaje": tiempoGrabando, "topic": "alsw/tiempo_obs"}
            objetoMQTTVertical: accion = accionMQTT()
            objetoMQTTVertical.configurar(opcionesVertical)
            objetoMQTTVertical.ejecutar()

            time.sleep(1)
        logger.info("OBS[Consulta Tiempo] - Terminado")

    def salvarFuente(self):
        # print("Hilo cargado Fuente " + str(threading.active_count()))
        if self.consultaCliente:
            logger.warning("Ya se esta salvando fuente")
            return

        if self.clienteConsultas is None:
            logger.warning("OBS[Fuente] Cliente de consultas no disponible")
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
        try:
            if not self.conectado or self.clienteConsultas is None:
                return

            escenaActual = self.clienteConsultas.get_scene_list()
            self.escenaActual = escenaActual.current_program_scene_name

            data = self.clienteConsultas.get_scene_item_list(self.escenaActual)
            if data is None:
                return

            for fuente in data.scene_items:
                idFuente = fuente.get("sceneItemId")
                nombreFuente = fuente.get("sourceName")
                estadoFuente = fuente.get("sceneItemEnabled")
                estadoFuenteViejo = ObtenerValor(unirPath(self.archivoEstado, "fuente"), nombreFuente)

                if estadoFuente != estadoFuenteViejo:
                    SalvarValor(unirPath(self.archivoEstado, "fuente"), nombreFuente, estadoFuente)
                    refrescar = True

                SalvarValor(unirPath(self.archivoEstado, "fuente_id"), [self.escenaActual, idFuente], nombreFuente)
                try:
                    self.SalvarFiltroFuente(nombreFuente)
                except Exception as error:
                    logger.warning(f"OBS[Filtro] Error salvando filtros de '{nombreFuente}': {error}")

            if refrescar:
                self.actualizarDeck()
        finally:
            self.consultaCliente = False

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
            self.enVivo = True
        else:
            self.Notificar("OBS-No-EnVivo")
            self.enVivo = False
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

        if self.clienteConsultas is None:
            logger.warning("OBS[Filtro] Cliente de consultas no disponible")
            return

        if not fuente:
            logger.warning("OBS[Filtro] Fuente vacia")
            return

        try:
            consultaFiltros = self.clienteConsultas.get_source_filter_list(fuente)
        except OBSerror.OBSSDKRequestError as error:
            logger.warning(f"OBS[Filtro] Consulta fallida para '{fuente}': {error}")
            return
        except Exception as error:
            logger.warning(f"OBS[Filtro] Error consultando filtros de '{fuente}': {error}")
            return

        if consultaFiltros is None:
            logger.debug(f"OBS[Filtro] Sin respuesta para '{fuente}'")
            return

        if hasattr(consultaFiltros, "filters"):
            filtros = consultaFiltros.filters
        elif isinstance(consultaFiltros, dict):
            filtros = consultaFiltros.get("filters")
        else:
            logger.warning(
                "OBS[Filtro] Respuesta inesperada para '%s': %s",
                fuente,
                type(consultaFiltros).__name__,
            )
            return

        if filtros is None:
            return

        dataFuenteAnterior = None
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

                SalvarValor(
                    unirPath(self.archivoEstado, "filtro_propiedades"),
                    [fuente, nombreFiltro, propiedad],
                    propiedadesFiltro[propiedad],
                )

    def on_vendor_event(self, mensaje):
        """Recibe mensajes de plugins extras"""
        vendedor = mensaje.vendor_name
        if vendedor == "aitum-vertical-canvas":
            # Documentación de eventos del plugin Vertical: https://github.com/Aitum/obs-vertical-canvas/blob/49885f17601e39e67b670614205824dfbec5ed29/vertical-canvas.cpp#L680
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
            self.grabandoVertical = True
            self.tiempoInicioVertical = time.time()
            SalvarValor(self.archivoEstado, "obs_grabar_vertical", True)
        elif tipo == "recording_stopping":
            self.Notificar("obs-no-grabando-vertival")
            self.grabandoVertical = False
            self.tiempoInicioVertical = None
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

    def cambiarEscena(self, escena: str):
        """Envía solicitud de cambiar de Escena."""
        try:
            self.clienteConsultas.set_current_program_scene(escena)
        except OBSerror.OBSSDKRequestError as e:
            logger.warning(f"OBS[No existe] {escena} {e}")
            self.Notificar(f"OBS[No existe] {escena}")
            return

        logger.info(f"OBS[Cambiando] {escena}")

    def cambiarFuente(self, fuente: str):
        """Envía solicitud de cambiar el estado de una fuente en la escena actual."""

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

    def cambiarFiltro(self, fuente: str, filtro: str, estado: bool | None = None):
        """Envía solicitud de cambiar estado de filtro, sin `estado` lo invierte."""
        if estado is None:
            estado = ObtenerValor(unirPath(self.archivoEstado, "filtro"), [fuente, filtro])
            if estado is None:
                logger.warning(f"OBS[Filtro sin estado] {fuente}[{filtro}]")
                return
            estado = not estado

        logger.info(f"OBS[Filtro] {fuente}[{filtro}]={estado}")
        self.clienteConsultas.set_source_filter_enabled(fuente, filtro, estado)

    def cambiarFiltroPropiedad(self, fuente: str, filtro: str, propiedad: str, valor, agregar: bool = False):
        """Envía solicitud de cambiar una propiedad de un filtro, con `agregar` suma al valor anterior."""
        PropiedadesAnteriores = ObtenerValor(unirPath(self.archivoEstado, "filtro_propiedades"), [fuente, filtro])

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

    def cambiarGrabacion(self):
        """Envía solicitud de cambiar estado de Grabación."""
        logger.info("Cambiando[Grabación]")
        try:
            self.clienteConsultas.toggle_record()
        except KeyError as e:
            logger.error(f"OBS[Error] {e}")

    def cambiarPausa(self):
        """Envía solicitud de cambiar estado de Pausa Grabación."""
        logger.info("Cambiando[Pausa]")
        self.clienteConsultas.toggle_record_pause()

    def cambiarEnVivo(self):
        """Envía solicitud de cambiar estado del Streaming."""
        logger.info("Cambiando[EnVivo]")
        self.clienteConsultas.toggle_stream()

    def cambiarCamaraVirtual(self):
        """Envía solicitud de cambio estado Cámara Virtual"""
        try:
            self.clienteConsultas.toggle_virtual_cam()
        except KeyError as e:
            logger.error(f"OBS[Error] {e}")

    def cambiarGrabacionVertical(self):
        """Envía solicitud de cambiar estado de Grabación en plugin Vertical."""
        logger.info("Cambiando[Grabación-Vertical]")
        try:
            self.clienteConsultas.call_vendor_request("aitum-vertical-canvas", "toggle_recording")
        except KeyError as e:
            if str(e) == "'requestStatus'":
                return
            logger.error(f"OBS[Error] {e}")

    def cambiarEnVivoVertical(self):
        """Envía solicitud de cambiar estado del Streaming en plugin Vertical."""
        logger.info("Cambiando[EnVivo-Vertical]")
        self.clienteConsultas.call_vendor_request("aitum-vertical-canvas", "toggle_streaming")

    def cambiarEscenaVertical(self, escena: str):
        """Envía solicitud de cambiar de Escena en plugin Vertical."""
        try:
            self.clienteConsultas.call_vendor_request("aitum-vertical-canvas", "switch_scene", {"scene": escena})
        except KeyError as e:
            # Captura el error específico de 'requestStatus'
            logger.error(f"OBS[Error-Vertical] La solicitud falló o hay una incompatibilidad de protocolo. Error: {e}")

        logger.info(f"OBS[Cambiando-Vertical] {escena}")

    def cambiarFuenteVertical(self, fuente: str, escena: str | None = None):
        """Envía solicitud de cambiar el estado de una fuente en el canvas del plugin Vertical.

        Si no se indica `escena` usa la escena vertical actual.
        """
        cliente = self.clienteConsultas
        try:
            if escena is None:
                consulta = {"vendorName": "aitum-vertical-canvas", "requestType": "current_scene"}
                escena = cliente.send("CallVendorRequest", consulta, raw=True)["responseData"]["scene"]
            # Por nombre OBS solo busca en el canvas principal, el vertical requiere sceneUuid (obs-websocket >= 5.7)
            canvas = cliente.send("GetCanvasList", raw=True)["canvases"]
            idCanvas = next(c["canvasUuid"] for c in canvas if c["canvasName"] == "Aitum Vertical")
            escenas = cliente.send("GetSceneList", {"canvasUuid": idCanvas}, raw=True)["scenes"]
            idEscena = next(e["sceneUuid"] for e in escenas if e["sceneName"] == escena)
            item = {"sceneUuid": idEscena}
            idFuente = cliente.send("GetSceneItemId", {**item, "sourceName": fuente}, raw=True)["sceneItemId"]
            item["sceneItemId"] = idFuente
            estado = cliente.send("GetSceneItemEnabled", item, raw=True)["sceneItemEnabled"]
            cliente.send("SetSceneItemEnabled", {**item, "sceneItemEnabled": not estado})
        except (StopIteration, OBSerror.OBSSDKRequestError) as e:
            logger.warning(f"OBS[No existe-Vertical] {escena}/{fuente} {e}")
            self.Notificar(f"OBS[No existe] {fuente}")
            return

        logger.info(f"OBS[Cambiando Fuente-Vertical] {escena}/{fuente} {not estado}")

    def TiempoGrabando(self, opciones=None):
        if self.conectado and self.clienteConsultas is not None:
            consulta = self.clienteConsultas.get_record_status()
            if consulta.output_active:
                tiempo = consulta.output_timecode.split(".")[0]
                logger.info(f"Tiempo Grabando: {tiempo}")
                return tiempo
        else:
            logger.info("OBS no Conectado")
            self.Notificar("OBS-No-Conectado")
        return "No-Grabando"

    def TiempoEnVivo(self, opciones=None):
        if self.conectado and self.clienteConsultas is not None:
            consulta = self.clienteConsultas.get_stream_status()
            if consulta.output_active:
                tiempo = consulta.output_timecode.split(".")[0]
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

    def desconectar(self):
        """Desconectar de OBS websocket."""
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
        """Recibe mensaje desconectar de OBS websocket."""
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
