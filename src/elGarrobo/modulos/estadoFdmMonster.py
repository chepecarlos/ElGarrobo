import threading
import time
from pathlib import Path
from typing import Any, Optional

import requests

from elGarrobo.accionesOOP.accionMQTT import accionMQTT
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerFolderConfig, SalvarArchivo
from elGarrobo.modulos.modulo import modulo

logger = ConfigurarLogging(__name__)

_CONFIGURACION_DEFECTO = {
    "url": "http://192.168.1.10:4000",
    "usuario": "admin",
    "clave": "",
    "intervalo_segundos": 30,
    "intervalo_error_segundos": 120,
    "limite_errores_log": 3,
}


class estadoFdmMonster(modulo):

    nombre = "estadoFdmMonster"
    modulo = "estado_fdm_monster"
    descripcion = "Módulo para obtener el estado de las impresoras de FDM Monster"

    archivoConfiguracion = "modulos/estado_fdm_monster.md"
    """Archivo de configuración del módulo.

    Formato esperado (un servidor FDM Monster, se monitorean todas sus impresoras habilitadas):
        url: http://192.168.50.200:4000
        usuario: admin
        clave: 1234
        intervalo_segundos: 30
        intervalo_error_segundos: 120
        limite_errores_log: 3

    Publica en MQTT: estado_fdm_monster/<nombre impresora>/<dato>
    y el total de trabajos en cola en: estado_fdm_monster/total/cola
    """

    def __init__(self, dataModulo: dict) -> None:
        super().__init__(dataModulo)
        self.activo = False
        self.hilo: Optional[threading.Thread] = None

        dataModulo = dataModulo or {}
        self._crear_configuracion_por_defecto()
        self.config = dataModulo

    def _crear_configuracion_por_defecto(self) -> None:
        archivoConfiguracion = Path(ObtenerFolderConfig()) / self.archivoConfiguracion

        if archivoConfiguracion.exists():
            return

        SalvarArchivo(str(archivoConfiguracion), dict(_CONFIGURACION_DEFECTO))
        logger.info(f"Modulo[{self.nombre}] - Archivo de configuración creado en {archivoConfiguracion}")

    def ejecutar(self) -> None:
        """Inicia un hilo que monitorea todas las impresoras del servidor FDM Monster."""
        if self.activo:
            return

        url = str(self.config.get("url", "")).strip().rstrip("/")
        if not url or not self.config.get("usuario"):
            logger.error(f"Modulo[{self.nombre}] - Falta 'url' o 'usuario', revisa {self.archivoConfiguracion}")
            return

        try:
            intervalo = max(5, int(self.config.get("intervalo_segundos", 30)))
        except (TypeError, ValueError):
            intervalo = 30

        try:
            intervalo_error = max(intervalo, int(self.config.get("intervalo_error_segundos", 120)))
        except (TypeError, ValueError):
            intervalo_error = 120

        try:
            limite_errores_log = max(1, int(self.config.get("limite_errores_log", 3)))
        except (TypeError, ValueError):
            limite_errores_log = 3

        self.activo = True
        self.hilo = threading.Thread(
            target=self._monitorear_estado,
            args=(f"{url}/api/v2", intervalo, intervalo_error, limite_errores_log),
            daemon=True,
            name="fdm-monster",
        )
        self.hilo.start()
        logger.info(f"Modulo[{self.nombre}] - Monitoreo iniciado cada {intervalo}s en {url}")

    def _iniciar_sesion(self, api: str) -> requests.Session:
        login = requests.post(
            f"{api}/auth/login",
            json={"username": self.config.get("usuario"), "password": self.config.get("clave")},
            timeout=10,
        )
        login.raise_for_status()
        sesion = requests.Session()
        sesion.headers["Authorization"] = f"Bearer {login.json()['token']}"
        return sesion

    def _normalizar_estado(self, payload: dict[str, Any]) -> dict[str, str]:
        # FDM Monster reenvía el estado en formato OctoPrint
        estado = payload.get("state") if isinstance(payload.get("state"), dict) else {}
        job = payload.get("job") if isinstance(payload.get("job"), dict) else {}
        archivo = job.get("file") if isinstance(job.get("file"), dict) else {}
        progreso = payload.get("progress") if isinstance(payload.get("progress"), dict) else {}

        porcentaje = progreso.get("completion")
        transcurrido = progreso.get("printTime")
        restante = progreso.get("printTimeLeft")

        porcentaje_valor = float(porcentaje) if isinstance(porcentaje, (int, float)) else 0.0
        transcurrido_seg = int(transcurrido) if isinstance(transcurrido, (int, float)) else 0
        if isinstance(restante, (int, float)):
            restante_seg = int(restante)
        else:
            # Moonraker no manda printTimeLeft, se estima por el progreso
            restante_seg = (
                int(transcurrido_seg / porcentaje_valor * (100 - porcentaje_valor)) if porcentaje_valor > 0 else 0
            )

        # Moonraker no manda state.text, se usa la primera bandera activa
        flags = estado.get("flags") if isinstance(estado.get("flags"), dict) else {}
        estado_flags = next(
            (f for f in ("error", "paused", "pausing", "cancelling", "printing", "operational") if flags.get(f)), None
        )

        return {
            "estado": str(estado.get("text") or estado_flags or "desconocido"),
            "archivo": str(archivo.get("display") or archivo.get("name") or ""),
            "progreso": f"{porcentaje_valor:.1f}",
            "tiempo_transcurrido": str(transcurrido_seg),
            "tiempo_restante": str(restante_seg),
            "tiempo_transcurrido_humano": self._formatear_tiempo(transcurrido_seg),
            "tiempo_restante_humano": self._formatear_tiempo(restante_seg),
        }

    def _normalizar_temperaturas(self, payload: dict[str, Any]) -> dict[str, str]:
        temps = payload.get("temps")
        if not isinstance(temps, list) or not temps or not isinstance(temps[-1], dict):
            return {}

        resultado: dict[str, str] = {}
        for sensor, datos in temps[-1].items():
            if not isinstance(datos, dict):
                continue
            for tipo in ("actual", "target"):
                if isinstance(datos.get(tipo), (int, float)):
                    resultado[f"{sensor}/{tipo}"] = f"{float(datos[tipo]):.1f}"
        return resultado

    def _obtener_json(self, sesion: requests.Session, url: str) -> Any:
        """GET que tolera body vacío (FDM Monster responde 200 sin contenido si no hay estado)."""
        respuesta = sesion.get(url, timeout=10)
        respuesta.raise_for_status()
        if not respuesta.content.strip():
            return {}
        try:
            return respuesta.json()
        except ValueError:
            raise ValueError(f"Respuesta no JSON de {url} [{respuesta.status_code}]: {respuesta.text[:100]!r}")

    def _publicar(self, topic: str, sub_topic: str, mensaje: str) -> None:
        topic_completo = f"estado_fdm_monster/{topic}/{sub_topic}"
        accionEnviar = accionMQTT()
        accionEnviar.configurar({"topic": topic_completo, "mensaje": str(mensaje)})
        accionEnviar.ejecutar()

    def _consultar_impresoras(self, sesion: requests.Session, api: str) -> int:
        """Publica el estado de cada impresora habilitada, devuelve cuántas respondieron."""
        impresoras = self._obtener_json(sesion, f"{api}/printer/") or []

        consultadas = 0
        cola_total = 0
        for impresora in impresoras:
            if not impresora.get("enabled"):
                continue
            nombre = str(impresora.get("name", impresora.get("id")))

            cola = self._obtener_json(sesion, f"{api}/print-queue/{impresora['id']}")
            cola_impresora = int(cola.get("count") or 0)
            cola_total += cola_impresora
            self._publicar(nombre, "cola", str(cola_impresora))

            socket = self._obtener_json(sesion, f"{api}/printer/{impresora['id']}/socket")
            current = socket.get("current") or {}
            payload = current.get("payload") if isinstance(current.get("payload"), dict) else None
            if payload is None:
                logger.debug(f"EstadoFdmMonster[{nombre}] - Sin estado disponible")
                continue

            estadoActual = self._normalizar_estado(payload)
            for sub_topic, valor in estadoActual.items():
                self._publicar(nombre, sub_topic, valor)
            for sub_topic, valor in self._normalizar_temperaturas(payload).items():
                self._publicar(nombre, f"temperatura/{sub_topic}", valor)

            logger.info(
                f"EstadoFdmMonster[{nombre}] - "
                f"Estado: {estadoActual['estado']} | "
                f"Progreso: {estadoActual['progreso']}% | "
                f"Transcurrido: {estadoActual['tiempo_transcurrido_humano']} | "
                f"Restante: {estadoActual['tiempo_restante_humano']} | "
                f"Cola: {cola_impresora}"
            )
            consultadas += 1

        self._publicar("total", "cola", str(cola_total))
        return consultadas

    def _monitorear_estado(self, api: str, intervalo: int, intervalo_error: int, limite_errores_log: int) -> None:
        errores_consecutivos = 0
        sesion: Optional[requests.Session] = None

        while self.activo:
            silenciar_error = errores_consecutivos >= limite_errores_log
            try:
                if sesion is None:
                    sesion = self._iniciar_sesion(api)
                self._consultar_impresoras(sesion, api)

                if errores_consecutivos >= limite_errores_log:
                    logger.info(f"Modulo[{self.nombre}] - Conexión recuperada")
                errores_consecutivos = 0

            except Exception as error:
                # ponytail: cualquier error (token vencido incluido) fuerza un nuevo login en el siguiente ciclo
                sesion = None
                errores_consecutivos += 1
                if not silenciar_error:
                    logger.error(f"Modulo[{self.nombre}] - Error en monitoreo: {error}")
                if errores_consecutivos == limite_errores_log:
                    logger.warning(
                        f"Modulo[{self.nombre}] - {limite_errores_log} errores seguidos, "
                        f"se silencian logs y se reintenta cada {intervalo_error}s"
                    )

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
        """Detiene el monitoreo."""
        self.activo = False
        logger.info(f"Modulo[{self.nombre}] - Monitoreo detenido")
