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
    "url": "http://octoprint.local",
    "token": "",
    "intervalo_segundos": 30,
}


class estadoOctoprint(modulo):

    nombre = "estadoOctoprint"
    modulo = "estado_octoprint"
    descripcion = "Módulo para obtener el estado de Octoprint"

    archivoConfiguracion = "modulos/estado_octoprint.md"
    """Archivo de configuración del módulo.

    Formato esperado (lista de impresoras):
        impresoras:
          - nombre: ender3
            topic: salon/ender3
            url: http://192.168.1.10:5000
            token: TU_API_KEY
            intervalo_segundos: 30
          - nombre: prusa
            topic: oficina/prusa
            url: http://192.168.1.11:5000
            token: TU_API_KEY
            intervalo_segundos: 30
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
            token = str(config.get("token", "")).strip()

            if not url or not token:
                logger.warning(f"EstadoOctoprint[{nombre}] - Falta 'url' o 'token', se omite esta impresora")
                continue

            try:
                intervalo = max(5, int(config.get("intervalo_segundos", 30)))
            except (TypeError, ValueError):
                intervalo = 30

            hilo = threading.Thread(
                target=self._monitorear_estado,
                args=(nombre, topic, url, token, intervalo),
                daemon=True,
                name=f"octoprint-{nombre}",
            )
            hilo.start()
            self.hilos.append(hilo)
            logger.info(f"EstadoOctoprint[{nombre}] - Monitoreo iniciado cada {intervalo}s en topic '{topic}'")

    def _normalizar_estado(self, payload: dict[str, Any]) -> dict[str, str]:
        progreso = payload.get("progress", {}) if isinstance(payload.get("progress"), dict) else {}

        # En OctoPrint, state viene como cadena directa: "Printing", "Paused", "Operational", etc.
        estado_raw = payload.get("state")
        estado_texto = str(estado_raw) if estado_raw else "desconocido"

        porcentaje = progreso.get("completion")
        tiempo_transcurrido = progreso.get("printTime")
        tiempo_restante = progreso.get("printTimeLeft")

        porcentaje_valor = float(porcentaje) if isinstance(porcentaje, (int, float)) else 0.0
        transcurrido_seg = int(tiempo_transcurrido) if isinstance(tiempo_transcurrido, (int, float)) else 0
        restante_seg = int(tiempo_restante) if isinstance(tiempo_restante, (int, float)) else 0

        return {
            "estado": estado_texto,
            "progreso": f"{porcentaje_valor:.1f}",
            "tiempo_transcurrido": str(transcurrido_seg),
            "tiempo_restante": str(restante_seg),
            "tiempo_transcurrido_humano": self._formatear_tiempo(transcurrido_seg),
            "tiempo_restante_humano": self._formatear_tiempo(restante_seg),
        }

    def _obtener_temperaturas_octoprint(self, nombre: str, url: str, token: str) -> Optional[dict[str, str]]:
        base_url = url.rstrip("/")
        endpoint = f"{base_url}/api/printer"
        headers = {"X-Api-Key": token}

        try:
            response = requests.get(endpoint, headers=headers, timeout=10)

            if response.status_code == 409:
                logger.info(f"EstadoOctoprint[{nombre}] - OctoPrint respondió 409 en temperaturas. " "Se intenta fallback por endpoints tool/bed")
                return self._obtener_temperaturas_fallback(nombre, base_url, headers)

            response.raise_for_status()
            payload = response.json()
            temps = payload.get("temperature", {})
            resultado: dict[str, str] = {}

            for sensor, datos in temps.items():
                if not isinstance(datos, dict):
                    continue
                actual = datos.get("actual")
                target = datos.get("target")
                if isinstance(actual, (int, float)):
                    resultado[f"{sensor}/actual"] = f"{float(actual):.1f}"
                if isinstance(target, (int, float)):
                    resultado[f"{sensor}/target"] = f"{float(target):.1f}"

            if not resultado:
                # Algunos servidores no exponen "temperature" en /api/printer pero sí en /api/printer/tool y /api/printer/bed
                return self._obtener_temperaturas_fallback(nombre, base_url, headers)

            logger.debug(f"EstadoOctoprint[{nombre}] - Temperaturas: {resultado}")
            return resultado
        except requests.RequestException as error:
            logger.error(f"EstadoOctoprint[{nombre}] - Error consultando temperaturas: {error}")
            return None
        except ValueError as error:
            logger.error(f"EstadoOctoprint[{nombre}] - JSON inválido en temperaturas: {error}")
            return None

    def _obtener_temperaturas_fallback(self, nombre: str, base_url: str, headers: dict[str, str]) -> Optional[dict[str, str]]:
        resultado: dict[str, str] = {}

        endpoints = {
            "tool": f"{base_url}/api/printer/tool",
            "bed": f"{base_url}/api/printer/bed",
        }

        for tipo, endpoint in endpoints.items():
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                if response.status_code == 409:
                    # 409 significa que OctoPrint no permite esta consulta en el estado actual.
                    continue
                response.raise_for_status()
                payload = response.json()

                if tipo == "tool":
                    for sensor, datos in payload.items():
                        if not isinstance(datos, dict):
                            continue
                        actual = datos.get("actual")
                        target = datos.get("target")
                        if isinstance(actual, (int, float)):
                            resultado[f"{sensor}/actual"] = f"{float(actual):.1f}"
                        if isinstance(target, (int, float)):
                            resultado[f"{sensor}/target"] = f"{float(target):.1f}"
                elif tipo == "bed":
                    bed = payload.get("bed", payload)
                    if isinstance(bed, dict):
                        actual = bed.get("actual")
                        target = bed.get("target")
                        if isinstance(actual, (int, float)):
                            resultado["bed/actual"] = f"{float(actual):.1f}"
                        if isinstance(target, (int, float)):
                            resultado["bed/target"] = f"{float(target):.1f}"
            except (requests.RequestException, ValueError):
                continue

        if not resultado:
            logger.debug(f"EstadoOctoprint[{nombre}] - Sin temperaturas disponibles por fallback")
            return None

        logger.debug(f"EstadoOctoprint[{nombre}] - Temperaturas fallback: {resultado}")
        return resultado

    def _obtener_estado_octoprint(self, nombre: str, url: str, token: str) -> Optional[dict[str, str]]:
        base_url = url.rstrip("/")
        endpoint = base_url if base_url.endswith("/api/job") else f"{base_url}/api/job"
        headers = {"X-Api-Key": token}

        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            payload = response.json()
            logger.debug(f"EstadoOctoprint[{nombre}] - Payload recibido: {payload}")
            return self._normalizar_estado(payload)
        except requests.RequestException as error:
            logger.error(f"EstadoOctoprint[{nombre}] - Error consultando {endpoint}: {error}")
            return None
        except ValueError as error:
            logger.error(f"EstadoOctoprint[{nombre}] - Respuesta JSON inválida: {error}")
            return None

    def _publicar(self, topic: str, sub_topic: str, mensaje: str) -> None:
        topic_completo = f"estado_octoprint/{topic}/{sub_topic}"
        accionEnviar = accionMQTT()
        accionEnviar.configurar({"topic": topic_completo, "mensaje": str(mensaje)})
        accionEnviar.ejecutar()

    def _monitorear_estado(self, nombre: str, topic: str, url: str, token: str, intervalo: int) -> None:
        while self.activo:
            try:
                estadoActual = self._obtener_estado_octoprint(nombre, url, token)
                if estadoActual:
                    self._publicar(topic, "estado", estadoActual["estado"])
                    self._publicar(topic, "progreso", estadoActual["progreso"])
                    self._publicar(topic, "tiempo_transcurrido", estadoActual["tiempo_transcurrido"])
                    self._publicar(topic, "tiempo_restante", estadoActual["tiempo_restante"])
                    self._publicar(topic, "tiempo_transcurrido_humano", estadoActual["tiempo_transcurrido_humano"])
                    self._publicar(topic, "tiempo_restante_humano", estadoActual["tiempo_restante_humano"])

                    logger.info(
                        f"EstadoOctoprint[{nombre}] - "
                        f"Estado: {estadoActual['estado']} | "
                        f"Progreso: {estadoActual['progreso']}% | "
                        f"Transcurrido: {estadoActual['tiempo_transcurrido_humano']} | "
                        f"Restante: {estadoActual['tiempo_restante_humano']}"
                    )

                temperaturas = self._obtener_temperaturas_octoprint(nombre, url, token)
                if temperaturas:
                    for sub_topic, valor in temperaturas.items():
                        self._publicar(topic, f"temperatura/{sub_topic}", valor)
                    logger.info(f"EstadoOctoprint[{nombre}] - Temperaturas: { {k: v for k, v in temperaturas.items()} }")

            except Exception as error:
                logger.error(f"EstadoOctoprint[{nombre}] - Error en monitoreo: {error}")

            time.sleep(intervalo)

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
