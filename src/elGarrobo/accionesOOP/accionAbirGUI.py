import logging
import socket

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase
from .accionNavegador import accionNavegador

Logger = ConfigurarLogging(__name__)


class accionAbirGUI(accionBase):
    """Esperar una cantidad de tiempo"""

    def __init__(self) -> None:
        nombre = "Abri GUI"
        comando = "abir_gui"
        descripcion = "Abri la Configuración del ElGarrobo en Navegador"
        super().__init__(nombre, comando, descripcion)

        self.funcion = self.abirGUI

    def abirGUI(self):
        """espera un tiempo"""
        tiempo = self.obtenerValor("tiempo")

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(("10.254.254.254", 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = "127.0.0.1"
        finally:
            s.close()

        url = f"{IP}:8080"
        Logger.info(f"Abriendo GUI {url}")
        acción = accionNavegador()
        acción.configurar({"url": url})
        acción.ejecutar()
