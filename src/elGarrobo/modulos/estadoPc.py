import threading
import time

import psutil

from elGarrobo.accionesOOP.accionMQTT import accionMQTT
from elGarrobo.miLibrerias import ConfigurarLogging
from elGarrobo.modulos.modulo import modulo

logger = ConfigurarLogging(__name__)


class estadoPc(modulo):

    nombre = "estadoPc"
    modulo = "estado_pc"
    descripcion = "Módulo para obtener el estado del PC"

    topicCPU: str = "umaru/cpu"
    topicRAM: str = "umaru/ram"

    hiloMonitoreo: threading.Thread
    """Módulo para obtener el estado del PC y monitorear recursos en segundo plano"""

    def __init__(self):
        super().__init__()
        self.activo = False
        self.hiloMonitoreo = None

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
                        "topic": self.topicCPU,
                        "mensaje": str(cpu),
                    }
                )
                accionEnviar.ejecutar()

                accionEnviar = accionMQTT()
                accionEnviar.configurar(
                    {
                        "topic": self.topicRAM,
                        "mensaje": str(memoria),
                    }
                )
                accionEnviar.ejecutar()

                logger.info(f"CPU: {cpu}% | Memoria: {memoria}%")
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                break

    def detener(self):
        """Detiene el monitoreo"""
        self.activo = False
        logger.info(f"Modulo[{self.nombre}] - Monitoreo detenido")
