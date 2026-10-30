import threading
import time
from typing import Any, Optional

import requests

from elGarrobo.modulos.octoprint.accionesOctoprint import accionCancelarOctoprint, accionReimprimirOctoprint
from elGarrobo.accionesOOP.accionMQTT import accionMQTT
from elGarrobo.miLibrerias import ConfigurarLogging
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.modulos.modulo import (
    eventoImpresion,
    eventosImpresion,
    faseOctoPrint,
    leerMonitoreo,
    modulo,
    propiedadesMonitoreo,
)

logger = ConfigurarLogging(__name__)


class moduloOctoprint(modulo):

    nombre = "Octoprint"
    modulo = "estado_octoprint"
    acciones = [accionReimprimirOctoprint, accionCancelarOctoprint]
    descripcion = "Módulo para obtener el estado de Octoprint"

    archivoConfiguracion = "modulos/estado_octoprint.md"
    propiedades = [
        propiedadAccion(
            nombre="Impresoras",
            atributo="impresoras",
            tipo=[list],
            descripcion="Impresoras a monitorear",
            elementos=[
                propiedadAccion(nombre="Nombre", atributo="nombre", tipo=[str], obligatorio=True, ejemplo="ender3"),
                propiedadAccion(
                    nombre="Topic",
                    atributo="topic",
                    tipo=[str],
                    descripcion="Topic MQTT, si no se indica usa el nombre",
                    ejemplo="salon/ender3",
                ),
                propiedadAccion(nombre="URL", atributo="url", tipo=[str], obligatorio=True, ejemplo="http://octoprint.local"),
                propiedadAccion(
                    nombre="Token",
                    atributo="token",
                    tipo=[str],
                    obligatorio=True,
                    descripcion="API key de Octoprint",
                    ejemplo="1234567890abcdef",
                ),
                *propiedadesMonitoreo(),
            ],
        )
    ]
    eventos = eventosImpresion(
        "octoprint",
        {
            "impresora": "ender3",
            "archivo": "pieza.gcode",
            "progreso": "100.0",
            "tiempo_transcurrido": "4980",
            "tiempo_transcurrido_humano": "1h 23m",
        },
    )

    def __init__(self, dataModulo: dict) -> None:
        super().__init__(dataModulo)
        self.activo = False
        self.hilos: list[threading.Thread] = []

        dataModulo = dataModulo or {}

        impresoras_raw = dataModulo.get("impresoras")
        self.impresoras: list[dict] = impresoras_raw if isinstance(impresoras_raw, list) else []
        self.fases: dict[str, str] = {}
        "impresora → fase en la lectura anterior, para avisar al cambiar"

    def ejecutar(self) -> None:
        """Inicia un hilo de monitoreo por cada impresora configurada."""
        if self.activo:
            return

        if not self.impresoras:
            logger.error(f"Modulo[{self.nombre}] - Sin impresoras configuradas, revisa {self.archivoConfiguracion}")
            return

        logger.info(f"Modulo[{self.nombre}] - {len(self.impresoras)} impresora(s) configuradas")
        self.activo = True
        # Para elegir la impresora del filtro en /eventos
        moduloOctoprint.valoresDatos = {"impresora": sorted(str(c.get("nombre", "")).strip() for c in self.impresoras)}
        for config in self.impresoras:
            nombre = str(config.get("nombre", "impresora-desconocida")).strip()
            topic = str(config.get("topic", nombre)).strip()
            url = str(config.get("url", "")).strip()
            token = str(config.get("token", "")).strip()

            if not url or not token:
                logger.warning(f"EstadoOctoprint[{nombre}] - Falta 'url' o 'token', se omite esta impresora")
                continue

            intervalo, intervalo_error, limite_errores_log = leerMonitoreo(config)

            hilo = threading.Thread(
                target=self._monitorear_estado,
                args=(nombre, topic, url, token, intervalo, intervalo_error, limite_errores_log),
                daemon=True,
                name=f"octoprint-{nombre}",
            )
            hilo.start()
            self.hilos.append(hilo)
            logger.info(f"EstadoOctoprint[{nombre}] - Monitoreo iniciado cada {intervalo}s en topic '{topic}'")

    def _normalizar_estado(self, payload: dict[str, Any]) -> dict[str, str]:
        progreso = payload.get("progress", {}) if isinstance(payload.get("progress"), dict) else {}
        trabajo = payload.get("job", {}) if isinstance(payload.get("job"), dict) else {}
        archivo = trabajo.get("file", {}) if isinstance(trabajo.get("file"), dict) else {}

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
            "archivo": str(archivo.get("name") or ""),
            "motivo": str(payload.get("error") or ""),
        }

    def _obtener_temperaturas_octoprint(self, nombre: str, url: str, token: str, silenciar_error: bool = False) -> Optional[dict[str, str]]:
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

            # logger.debug(f"EstadoOctoprint[{nombre}] - Temperaturas: {resultado}")
            return resultado
        except requests.RequestException as error:
            nivel = logger.debug if silenciar_error else logger.error
            nivel(f"EstadoOctoprint[{nombre}] - Error consultando temperaturas: {error}")
            return None
        except ValueError as error:
            nivel = logger.debug if silenciar_error else logger.error
            nivel(f"EstadoOctoprint[{nombre}] - JSON inválido en temperaturas: {error}")
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

        # logger.debug(f"EstadoOctoprint[{nombre}] - Temperaturas fallback: {resultado}")
        return resultado

    def _obtener_estado_octoprint(self, nombre: str, url: str, token: str, silenciar_error: bool = False) -> Optional[dict[str, str]]:
        base_url = url.rstrip("/")
        endpoint = base_url if base_url.endswith("/api/job") else f"{base_url}/api/job"
        headers = {"X-Api-Key": token}

        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            payload = response.json()
            # logger.debug(f"EstadoOctoprint[{nombre}] - Payload recibido: {payload}")
            return self._normalizar_estado(payload)
        except requests.RequestException as error:
            nivel = logger.debug if silenciar_error else logger.error
            nivel(f"EstadoOctoprint[{nombre}] - Error consultando {endpoint}: {error}")
            return None
        except ValueError as error:
            nivel = logger.debug if silenciar_error else logger.error
            nivel(f"EstadoOctoprint[{nombre}] - Respuesta JSON inválida: {error}")
            return None

    def _publicar(self, topic: str, sub_topic: str, mensaje: str) -> None:
        topic_completo = f"estado_octoprint/{topic}/{sub_topic}"
        accionEnviar = accionMQTT()
        accionEnviar.configurar({"topic": topic_completo, "mensaje": str(mensaje)})
        accionEnviar.ejecutar()

    def _monitorear_estado(
        self,
        nombre: str,
        topic: str,
        url: str,
        token: str,
        intervalo: int,
        intervalo_error: int,
        limite_errores_log: int,
    ) -> None:
        errores_consecutivos = 0

        while self.activo:
            silenciar_error = errores_consecutivos >= limite_errores_log
            try:
                estadoActual = self._obtener_estado_octoprint(nombre, url, token, silenciar_error)
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
                    self._avisarCambio(nombre, topic, estadoActual)

                temperaturas = self._obtener_temperaturas_octoprint(nombre, url, token, silenciar_error)
                if temperaturas:
                    for sub_topic, valor in temperaturas.items():
                        self._publicar(topic, f"temperatura/{sub_topic}", valor)
                    # logger.info(f"EstadoOctoprint[{nombre}] - Temperaturas: {temperaturas}")

                if estadoActual or temperaturas:
                    if errores_consecutivos >= limite_errores_log:
                        logger.info(f"EstadoOctoprint[{nombre}] - Conexión recuperada")
                    errores_consecutivos = 0
                else:
                    errores_consecutivos += 1
                    if errores_consecutivos == limite_errores_log:
                        logger.warning(f"EstadoOctoprint[{nombre}] - {limite_errores_log} errores seguidos, " f"se silencian logs y se reintenta cada {intervalo_error}s")

            except Exception as error:
                errores_consecutivos += 1
                if not silenciar_error:
                    logger.error(f"EstadoOctoprint[{nombre}] - Error en monitoreo: {error}")

            time.sleep(intervalo_error if errores_consecutivos >= limite_errores_log else intervalo)

    def _avisarCambio(self, nombre: str, topic: str, estadoActual: dict[str, str]) -> None:
        """Emite octoprint/<evento> si la impresora cambió de fase desde la lectura anterior"""
        anterior = self.fases.get(nombre)
        fase = faseOctoPrint(estadoActual["estado"], float(estadoActual["progreso"]), anterior)
        evento = eventoImpresion(anterior, fase)
        self.fases[nombre] = fase
        if evento:
            logger.info(f"EstadoOctoprint[{nombre}] - Evento {evento}")
            self._publicar(topic, "eventos", evento)
            self.emitirEvento(f"octoprint/{evento}", {"impresora": nombre, **estadoActual})

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
