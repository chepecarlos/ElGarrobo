import threading
import time
from pathlib import Path
from typing import Optional

import psutil

from elGarrobo.accionesOOP.accionMQTT import accionMQTT
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerFolderConfig, SalvarArchivo
from elGarrobo.modulos.modulo import modulo

logger = ConfigurarLogging(__name__)


class estadoPc(modulo):

    nombre = "estadoPc"
    modulo = "estado_pc"
    descripcion = "Módulo para obtener el estado del PC"

    topicCPU: str = "cpu"
    "Topic para publicar el uso de CPU"
    topicRAM: str = "ram"
    "Topic para publicar el uso de RAM"
    nombrePC: str = "pc-default"
    "Nombre del PC"
    archivoConfiguracion = "modulos/estado_pc.md"
    """Archivo de configuración del módulo"""

    hiloMonitoreo: Optional[threading.Thread]
    """Módulo para obtener el estado del PC y monitorear recursos en segundo plano"""

    def __init__(self, dataModulo: dict) -> None:
        super().__init__(dataModulo)
        self.activo = False
        self.hiloMonitoreo = None
        dataModulo = dataModulo or {}
        self._crear_configuracion_por_defecto(dataModulo)
        self.nombrePC = dataModulo.get("nombre_pc", self.nombrePC)

        if self.nombrePC == "pc-default":
            logger.warning(f"Estado[{self.nombrePC}] - No se especificó nombre del PC, " f"usando valor por defecto: {self.nombrePC}, " "edita el archivo de configuración para cambiarlo")

        logger.info(f"Estado[{self.nombrePC}] - Publicando estado de PC[{self.nombrePC}] por MQTT")

    def _crear_configuracion_por_defecto(self, dataModulo: dict) -> None:
        archivoConfiguracion = Path(ObtenerFolderConfig()) / self.archivoConfiguracion

        if archivoConfiguracion.exists():
            return

        nombre_pc = dataModulo.get("nombre_pc", self.nombrePC)
        dataDefecto = {"nombre_pc": nombre_pc}
        SalvarArchivo(str(archivoConfiguracion), dataDefecto)
        if "nombre_pc" not in dataModulo:
            dataModulo.update(dataDefecto)
        logger.info(f"Modulo[{self.nombre}] - Archivo de configuración creado en {archivoConfiguracion}")

    def ejecutar(self) -> None:
        """Obtiene el estado actual del PC"""

        if self.activo:
            return

        self.activo = True
        self.hiloMonitoreo = threading.Thread(target=self._monitorear_recursos, daemon=True)
        self.hiloMonitoreo.start()
        logger.info(f"Modulo[{self.nombre}] - Monitoreo iniciado")

    def _monitorear_recursos(self):
        """Imprime CPU y memoria cada 10 segundos en un hilo separado"""
        while self.activo:
            try:
                cpu = psutil.cpu_percent(interval=1)
                memoria = psutil.virtual_memory().percent

                accionEnviar = accionMQTT()
                accionEnviar.configurar(
                    {
                        "topic": f"estado_pc/{self.nombrePC}/{self.topicCPU}",
                        "mensaje": str(cpu),
                    }
                )
                accionEnviar.ejecutar()

                accionEnviar = accionMQTT()
                accionEnviar.configurar(
                    {
                        "topic": f"estado_pc/{self.nombrePC}/{self.topicRAM}",
                        "mensaje": str(memoria),
                    }
                )
                accionEnviar.ejecutar()

                logger.info(f"Estado[{self.nombrePC}] - CPU: {cpu}% | Memoria: {memoria}%")
                time.sleep(10)
            except Exception as e:
                logger.error(f"Estado[{self.nombrePC}] - Error en monitoreo: {e}")
                break

    def detener(self):
        """Detiene el monitoreo"""
        self.activo = False
        logger.info(f"Estado[{self.nombrePC}] - Monitoreo detenido")
