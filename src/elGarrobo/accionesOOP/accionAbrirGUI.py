"""Abre la interface de ElGarrobo en el Navegador"""

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerArchivo

from .accion import accion
from .accionNavegador import accionNavegador

Logger = ConfigurarLogging(__name__)


def obtenerPuertoGUI() -> int:
    """Puerto de la primera GUI activada en gui.md, mismo default que miGui"""
    for gui in ObtenerArchivo("gui.md") or []:
        if gui.get("activado", True):
            return gui.get("puerto", 8080)
    return 8080


class accionAbrirGUI(accion):
    """Abre la interface web del ElGarrobo"""

    nombre = "Abrir GUI"
    comando = "abrir_gui"
    descripcion = "Abrir la Configuración del ElGarrobo en Navegador"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.funcion = self.abrirGUI

    def abrirGUI(self):
        """Abre la interface en el Navegador"""

        url = f"http://localhost:{obtenerPuertoGUI()}"
        Logger.info(f"Abriendo GUI {url}")
        acción: accionNavegador = accionNavegador()
        acción.configurar({"url": url})
        acción.ejecutar()
