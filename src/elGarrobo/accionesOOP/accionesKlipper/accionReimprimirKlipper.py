"""Acción para reimprimir el último trabajo en Klipper (Moonraker)"""

import requests

from elGarrobo.accionesOOP.accion import accion, propiedadAccion
from elGarrobo.accionesOOP.accionNotificacion import accionNotificacion
from elGarrobo.miLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


class accionReimprimirKlipper(accion):
    """Reimprime el último trabajo en Klipper usando la API de Moonraker"""

    nombre = "Reimprimir Klipper"
    comando = "reimprimir_klipper"
    descripcion = "Reimprime el último trabajo en Klipper (Moonraker)"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadURL = propiedadAccion(
            nombre="URL",
            atributo="url",
            tipo=[str],
            obligatorio=True,
            descripcion="URL de Moonraker",
            ejemplo="http://192.168.1.10:7125",
        )

        propiedadToken = propiedadAccion(
            nombre="Token",
            atributo="token",
            tipo=[str],
            obligatorio=False,
            descripcion="API key de Moonraker (si tiene autenticación activada)",
            ejemplo="1234567890abcdef",
        )

        self.agregarPropiedad(propiedadURL)
        self.agregarPropiedad(propiedadToken)

        self.funcion = self.reimprimirTrabajo

    def notificar(self, texto: str) -> None:
        notificación = accionNotificacion()
        notificación.configurar({"texto": texto})
        notificación.ejecutar()

    def reimprimirTrabajo(self):
        """Busca el último archivo impreso en el historial y lo vuelve a iniciar"""
        base_url = str(self.obtenerValor("url")).strip().rstrip("/")
        token = self.obtenerValor("token")
        headers = {"X-Api-Key": str(token).strip()} if token else {}

        try:
            response = requests.get(f"{base_url}/server/history/list", headers=headers, params={"limit": 1}, timeout=10)
            response.raise_for_status()
            trabajos = response.json().get("result", {}).get("jobs", [])
            if not trabajos:
                Logger.error(f"Klipper[Error] No hay trabajos en el historial de {base_url}")
                self.notificar(f"Klipper[Error] No hay trabajos en el historial de {base_url}")
                return

            archivo = trabajos[0]["filename"]
            response = requests.post(f"{base_url}/printer/print/start", headers=headers, params={"filename": archivo}, timeout=10)
            response.raise_for_status()

            Logger.info(f"Klipper[OK] Reimpresión de {archivo} enviada a {base_url}")
            self.notificar(f"Klipper[OK] Reimpresión de {archivo} enviada a {base_url}")

        except requests.RequestException as error:
            detalle = (getattr(error.response, "text", "") or str(error)).strip()[:300]
            Logger.error(f"Klipper[Error] {base_url}: {detalle}")
            self.notificar(f"Klipper[Error] {base_url}: {detalle}")
