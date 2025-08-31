"""Abre la interface de ElGarrobo en el Navegador"""

import logging
import socket

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase
from .accionNavegador import accionNavegador

Logger = ConfigurarLogging(__name__)


class accionAbirGUI(accionBase):
    """Abre la interface web del ElGarrobo"""

    nombre = "Abri GUI"
    comando = "abir_gui"
    descripcion = "Abri la Configuración del ElGarrobo en Navegador"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.funcion = self.abirGUI

    def abirGUI(self):
        """Abre la interface en el Navegador"""

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

        url = f"{IP}:8181"
        Logger.info(f"Abriendo GUI {url}")
        acción: accionNavegador = accionNavegador()
        acción.configurar({"url": url})
        acción.ejecutar()
