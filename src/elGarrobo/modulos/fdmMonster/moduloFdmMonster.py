import json
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

import requests

from elGarrobo.modulos.fdmMonster.accionesFdmMonster import accionImprimirColaFDM
from elGarrobo.accionesOOP.accionMQTT import accionMQTT
from elGarrobo.miLibrerias import ConfigurarLogging
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.modulos.modulo import eventoModulo, leerMonitoreo, modulo, propiedadesMonitoreo

logger = ConfigurarLogging(__name__)

DATOS_TRABAJO = {
    "impresora": "CoreOne",
    "archivo": "pieza_0.2mm_PLA.gcode",
    "tiempo_transcurrido": "4980",
    "tiempo_transcurrido_humano": "1h 23m",
}
"Datos de los eventos de un trabajo, con valores de ejemplo"

EVENTOS_ESTADO = {
    "PRINTING": "impresion_iniciada",
    "COMPLETED": "impresion_terminada",
    "CANCELLED": "impresion_cancelada",
}
"status de un trabajo de FDM Monster → evento; FAILED depende del motivo y PENDING/UNKNOWN no avisan"


class moduloFdmMonster(modulo):

    nombre = "estadoFdmMonster"
    modulo = "estado_fdm_monster"
    acciones = [accionImprimirColaFDM]
    descripcion = "Módulo para obtener el estado de las impresoras de FDM Monster"

    archivoConfiguracion = "modulos/estado_fdm_monster.md"
    """Archivo de configuración del módulo, se monitorean todas las impresoras habilitadas del servidor.

    Publica en MQTT: estado_fdm_monster/<nombre impresora>/<dato>,
    el total de trabajos en cola en: estado_fdm_monster/total/cola
    y cada evento (ej. impresion_terminada) en: estado_fdm_monster/<nombre impresora>/eventos
    """
    propiedades = [
        propiedadAccion(nombre="URL", atributo="url", tipo=[str], obligatorio=True, ejemplo="http://192.168.1.10:4000"),
        propiedadAccion(nombre="Usuario", atributo="usuario", tipo=[str], obligatorio=True, ejemplo="admin"),
        propiedadAccion(nombre="Clave", atributo="clave", tipo=[str], descripcion="Contraseña de FDM Monster"),
        *propiedadesMonitoreo(),
        propiedadAccion(
            nombre="Duración mínima para avisar",
            atributo="duracion_minima_segundos",
            tipo=[int],
            descripcion="Trabajos terminados más cortos no avisan (PrusaLink crea trabajos fantasma de milisegundos)",
            defecto=30,
        ),
        propiedadAccion(
            nombre="Espera entre eventos repetidos",
            atributo="espera_repetidos_segundos",
            tipo=[int],
            descripcion="Segundos antes de repetir el mismo evento en la misma impresora",
            defecto=60,
        ),
    ]
    eventos = [
        eventoModulo("fdm_monster/impresion_iniciada", "Una impresora empezó a imprimir", DATOS_TRABAJO),
        eventoModulo("fdm_monster/impresion_terminada", "Una impresora terminó de imprimir", DATOS_TRABAJO),
        eventoModulo(
            "fdm_monster/impresion_cancelada", "Se canceló una impresión", DATOS_TRABAJO | {"motivo": "Cancelled"}
        ),
        eventoModulo(
            "fdm_monster/impresion_error",
            "Una impresión falló",
            DATOS_TRABAJO | {"motivo": "Print submission failed: timeout of 30000ms exceeded"},
        ),
        eventoModulo(
            "fdm_monster/impresion_pausada",
            "Una impresora pausó la impresión",
            {
                "impresora": "CoreOne",
                "estado": "Paused",
                "archivo": "pieza_0.2mm_PLA.gcode",
                "progreso": "42.0",
                "tiempo_transcurrido": "4980",
                "tiempo_restante": "6900",
                "tiempo_transcurrido_humano": "1h 23m",
                "tiempo_restante_humano": "1h 55m",
            },
        ),
    ]

    def __init__(self, dataModulo: dict) -> None:
        super().__init__(dataModulo)
        self.activo = False
        self.hilo: Optional[threading.Thread] = None

        dataModulo = dataModulo or {}
        self.config = dataModulo

        self.trabajos: Optional[dict[int, str]] = None
        "id → status de los trabajos de la consulta anterior; None hasta la primera, que solo guarda sin avisar"
        self.ultimoTrabajo = 0
        "id más alto visto, para no tomar como nuevo un trabajo viejo que entra a la página"
        self.pausadas: dict[str, bool] = {}
        "impresora → si estaba pausada en la consulta anterior"
        self.ultimosEventos: dict[tuple[str, str], float] = {}
        "(impresora, evento) → cuándo se avisó, para no repetirlo seguido"
        self.duracionMinima = self._leerEntero("duracion_minima_segundos")
        self.esperaRepetidos = self._leerEntero("espera_repetidos_segundos")

    def _leerEntero(self, atributo: str) -> int:
        """Opción entera del archivo; si falta o no es válida usa el defecto de `propiedades`"""
        defecto = next(p.defecto for p in self.propiedades if p.atributo == atributo)
        try:
            return int(self.config.get(atributo, defecto))
        except (TypeError, ValueError):
            return defecto

    def ejecutar(self) -> None:
        """Inicia un hilo que monitorea todas las impresoras del servidor FDM Monster."""
        if self.activo:
            return

        url = str(self.config.get("url", "")).strip().rstrip("/")
        if not url or not self.config.get("usuario"):
            logger.error(f"Modulo[{self.nombre}] - Falta 'url' o 'usuario', revisa {self.archivoConfiguracion}")
            return

        intervalo, intervalo_error, limite_errores_log = leerMonitoreo(self.config)

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
        nombres = [str(i.get("name", i.get("id"))) for i in impresoras if i.get("enabled")]
        # Para elegir la impresora del filtro en /eventos sin escribir su nombre a mano
        moduloFdmMonster.valoresDatos = {"impresora": sorted(nombres)}
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
            # "Pausing" y "Paused": avisa una vez al entrar; la primera consulta solo guarda
            pausada = "paus" in estadoActual["estado"].lower()
            if pausada and self.pausadas.get(nombre) is False:
                self._emitir("impresion_pausada", {"impresora": nombre, **estadoActual})
            self.pausadas[nombre] = pausada
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

    def _revisar_trabajos(self, sesion: requests.Session, api: str) -> None:
        """Avisa los trabajos que cambiaron de status desde la consulta anterior (iniciada, terminada, error...)"""
        # La página trae primero los que imprimen y después los más nuevos.
        # ponytail: 20 por consulta; si entre consultas aparecen más trabajos nuevos, los más viejos de esos no avisan
        pagina = self._obtener_json(sesion, f"{api}/print-jobs/search-paged?page=1&pageSize=20")
        trabajos = {trabajo["id"]: trabajo for trabajo in pagina.get("items", [])}
        anteriores = self.trabajos
        for idTrabajo, status in (anteriores or {}).items():
            # Al terminar sale de la página: los fantasma de PrusaLink son más nuevos y lo empujan
            if status == "PRINTING" and idTrabajo not in trabajos:
                try:
                    trabajos[idTrabajo] = self._obtener_json(sesion, f"{api}/print-jobs/{idTrabajo}")
                except requests.HTTPError as error:
                    # Ej. borrado del historial: se deja de seguir
                    logger.warning(f"EstadoFdmMonster - Trabajo {idTrabajo} no disponible: {error}")

        ultimo = self.ultimoTrabajo
        self.trabajos = {idTrabajo: trabajo.get("status") for idTrabajo, trabajo in trabajos.items()}
        self.ultimoTrabajo = max([ultimo, *trabajos])
        if anteriores is None:
            return

        for idTrabajo, trabajo in sorted(trabajos.items()):
            anterior = anteriores.get(idTrabajo)
            if trabajo.get("status") == anterior or (anterior is None and idTrabajo <= ultimo):
                # Sin cambio, o un trabajo viejo que entró a la página porque otro salió
                continue
            evento = self._evento_trabajo(trabajo)
            if evento is None:
                continue
            datos, duracion = self._datos_trabajo(trabajo)
            if evento != "impresion_iniciada" and duracion is not None and duracion < self.duracionMinima:
                logger.debug(f"EstadoFdmMonster - Trabajo {idTrabajo} de {duracion}s ignorado ({evento})")
                continue
            self._emitir(evento, datos)

    @staticmethod
    def _evento_trabajo(trabajo: dict[str, Any]) -> Optional[str]:
        if trabajo.get("status") == "FAILED":
            # FDM Monster guarda la cancelación de OctoPrint como FAILED con motivo "Cancelled"
            return "impresion_cancelada" if trabajo.get("statusReason") == "Cancelled" else "impresion_error"
        return EVENTOS_ESTADO.get(trabajo.get("status"))

    def _datos_trabajo(self, trabajo: dict[str, Any]) -> tuple[dict[str, str], Optional[int]]:
        """Datos del evento y duración en segundos si ya terminó (None si sigue o no hay fechas)"""
        inicio, fin = (self._fecha(trabajo.get(campo)) for campo in ("startedAt", "endedAt"))
        segundos = int(((fin or datetime.now(timezone.utc)) - inicio).total_seconds()) if inicio else 0
        datos = {
            "impresora": str(trabajo.get("printerName") or trabajo.get("printerId")),
            "archivo": str(trabajo.get("fileName") or ""),
            "tiempo_transcurrido": str(segundos),
            "tiempo_transcurrido_humano": self._formatear_tiempo(segundos),
        }
        if trabajo.get("status") in ("FAILED", "CANCELLED"):
            datos["motivo"] = self._motivo(trabajo.get("statusReason"))
        return datos, segundos if inicio and fin else None

    @staticmethod
    def _fecha(texto: Any) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _motivo(texto: Any) -> str:
        """'Print submission failed: {"error":"timeout...","stack":...}' → 'Print submission failed: timeout...'"""
        texto = str(texto or "")
        prefijo, _, resto = texto.partition(": ")
        try:
            return f"{prefijo}: {json.loads(resto)['error']}"
        except (ValueError, KeyError, TypeError):
            return texto[:200]

    def _emitir(self, evento: str, datos: dict[str, str]) -> None:
        """Publica el evento en MQTT y dispara sus acciones, salvo si se avisó hace poco en la misma impresora"""
        clave = (datos["impresora"], evento)
        ahora = time.monotonic()
        if clave in self.ultimosEventos and ahora - self.ultimosEventos[clave] < self.esperaRepetidos:
            logger.info(f"EstadoFdmMonster[{datos['impresora']}] - {evento} repetido, no se avisa")
            return
        self.ultimosEventos[clave] = ahora
        logger.info(f"EstadoFdmMonster[{datos['impresora']}] - Evento {evento}")
        self._publicar(datos["impresora"], "eventos", evento)
        self.emitirEvento(f"fdm_monster/{evento}", datos)

    def _monitorear_estado(self, api: str, intervalo: int, intervalo_error: int, limite_errores_log: int) -> None:
        errores_consecutivos = 0
        sesion: Optional[requests.Session] = None

        while self.activo:
            silenciar_error = errores_consecutivos >= limite_errores_log
            try:
                if sesion is None:
                    sesion = self._iniciar_sesion(api)
                self._consultar_impresoras(sesion, api)
                self._revisar_trabajos(sesion, api)

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
