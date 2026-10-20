import threading
import time
from typing import Optional

import psutil

from elGarrobo.accionesOOP.accionMQTT import accionMQTT
from elGarrobo.miLibrerias import ConfigurarLogging
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
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
    propiedades = [
        propiedadAccion(
            nombre="Nombre del PC",
            atributo="nombre_pc",
            tipo=[str],
            obligatorio=True,
            descripcion="Se usa en los topics MQTT: estado_pc/<nombre>/cpu",
            ejemplo="mi-pc",
            defecto="pc-default",
        )
    ]

    hiloMonitoreo: Optional[threading.Thread]
    """Módulo para obtener el estado del PC y monitorear recursos en segundo plano"""

    def __init__(self, dataModulo: dict) -> None:
        super().__init__(dataModulo)
        self.activo = False
        self.hiloMonitoreo = None
        dataModulo = dataModulo or {}
        self.nombrePC = dataModulo.get("nombre_pc", self.nombrePC)

        if self.nombrePC == "pc-default":
            logger.warning(f"Estado[{self.nombrePC}] - No se especificó nombre del PC, " f"usando valor por defecto: {self.nombrePC}, " "cámbialo en la GUI en /modulos")

        logger.info(f"Estado[{self.nombrePC}] - Publicando estado de PC[{self.nombrePC}] por MQTT")

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
