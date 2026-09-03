import threading
import time
from pathlib import Path
from typing import Any, Optional

import requests

from elGarrobo.accionesOOP.accionMQTT import accionMQTT
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerFolderConfig, SalvarArchivo
from elGarrobo.modulos.modulo import modulo

logger = ConfigurarLogging(__name__, 10)

_IMPRESORA_DEFECTO = {
    "nombre": "impresora-1",
    "topic": "impresora-1",
    "url": "http://192.168.1.10:7125",
    "intervalo_segundos": 30,
    "intervalo_error_segundos": 120,
    "limite_errores_log": 3,
}

_OBJETOS_QUERY = {"print_stats": "", "virtual_sdcard": "", "toolhead": "", "extruder": "", "heater_bed": ""}


class estadoKlipper(modulo):

    nombre = "estadoKlipper"
    modulo = "estado_klipper"
    descripcion = "Módulo para obtener el estado de una impresora Klipper (Moonraker)"

    archivoConfiguracion = "modulos/estado_klipper.md"
    """Archivo de configuración del módulo.

    Formato esperado (lista de impresoras):
        impresoras:
          - nombre: ender3
            topic: salon/ender3
            url: http://192.168.1.10:7125
            intervalo_segundos: 30
          - nombre: voron
            topic: oficina/voron
            url: http://192.168.1.11:7125
            intervalo_segundos: 30
            intervalo_error_segundos: 120
            limite_errores_log: 3
    """

    def __init__(self, dataModulo: dict) -> None:
        super().__init__(dataModulo)
        self.activo = False
        self.hilos: list[threading.Thread] = []

        dataModulo = dataModulo or {}
        self._crear_configuracion_por_defecto(dataModulo)

        impresoras_raw = dataModulo.get("impresoras")
        self.impresoras: list[dict] = impresoras_raw if isinstance(impresoras_raw, list) else []

        if not self.impresoras:
            logger.warning(f"Modulo[{self.nombre}] - No hay impresoras configuradas en 'impresoras'")
        else:
            logger.info(f"Modulo[{self.nombre}] - {len(self.impresoras)} impresora(s) configuradas")

    def _crear_configuracion_por_defecto(self, dataModulo: dict) -> None:
        archivoConfiguracion = Path(ObtenerFolderConfig()) / self.archivoConfiguracion

        if archivoConfiguracion.exists():
            return

        dataDefecto = {"impresoras": [dict(_IMPRESORA_DEFECTO)]}
        SalvarArchivo(str(archivoConfiguracion), dataDefecto)
        logger.info(f"Modulo[{self.nombre}] - Archivo de configuración creado en {archivoConfiguracion}")

    def ejecutar(self) -> None:
        """Inicia un hilo de monitoreo por cada impresora configurada."""
        if self.activo:
            return

        if not self.impresoras:
            logger.error(f"Modulo[{self.nombre}] - Sin impresoras configuradas, revisa {self.archivoConfiguracion}")
            return

        self.activo = True
        for config in self.impresoras:
            nombre = str(config.get("nombre", "impresora-desconocida")).strip()
            topic = str(config.get("topic", nombre)).strip()
            url = str(config.get("url", "")).strip()

            if not url:
                logger.warning(f"EstadoKlipper[{nombre}] - Falta 'url', se omite esta impresora")
                continue

            try:
                intervalo = max(5, int(config.get("intervalo_segundos", 30)))
            except (TypeError, ValueError):
                intervalo = 30

            try:
                intervalo_error = max(intervalo, int(config.get("intervalo_error_segundos", 120)))
            except (TypeError, ValueError):
                intervalo_error = 120

            try:
                limite_errores_log = max(1, int(config.get("limite_errores_log", 3)))
            except (TypeError, ValueError):
                limite_errores_log = 3

            hilo = threading.Thread(
                target=self._monitorear_estado,
                args=(nombre, topic, url, intervalo, intervalo_error, limite_errores_log),
                daemon=True,
                name=f"klipper-{nombre}",
            )
            hilo.start()
            self.hilos.append(hilo)
            logger.info(f"EstadoKlipper[{nombre}] - Monitoreo iniciado cada {intervalo}s en topic '{topic}'")

    def _normalizar_estado(self, status: dict[str, Any]) -> dict[str, str]:
        print_stats = status.get("print_stats", {}) if isinstance(status.get("print_stats"), dict) else {}
        info = print_stats.get("info", {}) if isinstance(print_stats.get("info"), dict) else {}
        virtual_sdcard = status.get("virtual_sdcard", {}) if isinstance(status.get("virtual_sdcard"), dict) else {}

        estado_raw = print_stats.get("state")
        estado_texto = str(estado_raw) if estado_raw else "desconocido"

        progreso_fraccion = virtual_sdcard.get("progress")
        porcentaje = float(progreso_fraccion) * 100 if isinstance(progreso_fraccion, (int, float)) else 0.0

        transcurrido_seg = int(print_stats.get("print_duration") or 0)
        restante_seg = int(transcurrido_seg / porcentaje * (100 - porcentaje)) if porcentaje > 0 else 0

        return {
            "estado": estado_texto,
            "archivo": str(print_stats.get("filename", "")),
            "capa_actual": str(info.get("current_layer") or 0),
            "capa_total": str(info.get("total_layer") or 0),
            "progreso": f"{porcentaje:.1f}",
            "tiempo_transcurrido": str(transcurrido_seg),
            "tiempo_restante": str(restante_seg),
            "tiempo_impresion": self._formatear_tiempo(transcurrido_seg),
            "tiempo_restante_humano": self._formatear_tiempo(restante_seg),
        }

    def _normalizar_temperaturas(self, status: dict[str, Any]) -> dict[str, str]:
        resultado: dict[str, str] = {}

        extruder = status.get("extruder", {}) if isinstance(status.get("extruder"), dict) else {}
        if isinstance(extruder.get("temperature"), (int, float)):
            resultado["extruder/actual"] = f"{float(extruder['temperature']):.1f}"
        if isinstance(extruder.get("target"), (int, float)):
            resultado["extruder/target"] = f"{float(extruder['target']):.1f}"

        heater_bed = status.get("heater_bed", {}) if isinstance(status.get("heater_bed"), dict) else {}
        if isinstance(heater_bed.get("temperature"), (int, float)):
            resultado["bed/actual"] = f"{float(heater_bed['temperature']):.1f}"
        if isinstance(heater_bed.get("target"), (int, float)):
            resultado["bed/target"] = f"{float(heater_bed['target']):.1f}"

        return resultado

    def _obtener_estado_klipper(self, nombre: str, url: str, silenciar_error: bool = False) -> Optional[dict[str, Any]]:
        base_url = url.rstrip("/")
        endpoint = f"{base_url}/printer/objects/query"

        try:
            response = requests.get(endpoint, params=_OBJETOS_QUERY, timeout=10)
            response.raise_for_status()
            payload = response.json()
            status = payload.get("result", {}).get("status", {})
            return status
        except requests.RequestException as error:
            nivel = logger.debug if silenciar_error else logger.error
            nivel(f"EstadoKlipper[{nombre}] - Error consultando {endpoint}: {error}")
            return None
        except ValueError as error:
            nivel = logger.debug if silenciar_error else logger.error
            nivel(f"EstadoKlipper[{nombre}] - Respuesta JSON inválida: {error}")
            return None

    def _publicar(self, topic: str, sub_topic: str, mensaje: str) -> None:
        topic_completo = f"estado_klipper/{topic}/{sub_topic}"
        accionEnviar = accionMQTT()
        accionEnviar.configurar({"topic": topic_completo, "mensaje": str(mensaje)})
        accionEnviar.ejecutar()

    def _monitorear_estado(
        self,
        nombre: str,
        topic: str,
        url: str,
        intervalo: int,
        intervalo_error: int,
        limite_errores_log: int,
    ) -> None:
        errores_consecutivos = 0

        while self.activo:
            silenciar_error = errores_consecutivos >= limite_errores_log
            try:
                status = self._obtener_estado_klipper(nombre, url, silenciar_error)

                if status:
                    estadoActual = self._normalizar_estado(status)
                    temperaturas = self._normalizar_temperaturas(status)

                    self._publicar(topic, "estado", estadoActual["estado"])
                    self._publicar(topic, "archivo", estadoActual["archivo"])
                    self._publicar(topic, "capa_actual", estadoActual["capa_actual"])
                    self._publicar(topic, "capa_total", estadoActual["capa_total"])
                    self._publicar(topic, "progreso", estadoActual["progreso"])
                    self._publicar(topic, "tiempo_transcurrido", estadoActual["tiempo_transcurrido"])
                    self._publicar(topic, "tiempo_restante", estadoActual["tiempo_restante"])
                    self._publicar(topic, "tiempo_impresion", estadoActual["tiempo_impresion"])
                    self._publicar(topic, "tiempo_restante_humano", estadoActual["tiempo_restante_humano"])

                    for sub_topic, valor in temperaturas.items():
                        self._publicar(topic, f"temperatura/{sub_topic}", valor)

                    logger.info(
                        f"EstadoKlipper[{nombre}] - "
                        f"Estado: {estadoActual['estado']} | "
                        f"Progreso: {estadoActual['progreso']}% | "
                        f"Capa: {estadoActual['capa_actual']}/{estadoActual['capa_total']} | "
                        f"Transcurrido: {estadoActual['tiempo_impresion']} | "
                        f"Restante: {estadoActual['tiempo_restante_humano']}"
                    )

                    if errores_consecutivos >= limite_errores_log:
                        logger.info(f"EstadoKlipper[{nombre}] - Conexión recuperada")
                    errores_consecutivos = 0
                else:
                    errores_consecutivos += 1
                    if errores_consecutivos == limite_errores_log:
                        logger.warning(f"EstadoKlipper[{nombre}] - {limite_errores_log} errores seguidos, " f"se silencian logs y se reintenta cada {intervalo_error}s")

            except Exception as error:
                errores_consecutivos += 1
                if not silenciar_error:
                    logger.error(f"EstadoKlipper[{nombre}] - Error en monitoreo: {error}")

            time.sleep(intervalo_error if errores_consecutivos >= limite_errores_log else intervalo)

    def _formatear_tiempo(self, segundos: int) -> str:
        if segundos <= 0:
            return "0m"

        horas = segundos // 3600
        minutos = (segundos % 3600) // 60

        if horas > 0:
            return f"{horas}h {minutos}m"
        return f"{minutos}m"

    def detener(self) -> None:
        """Detiene el monitoreo de todas las impresoras."""
        self.activo = False
        logger.info(f"Modulo[{self.nombre}] - Monitoreo detenido ({len(self.hilos)} hilo(s))")
