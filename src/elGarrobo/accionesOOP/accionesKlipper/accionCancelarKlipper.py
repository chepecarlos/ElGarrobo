"""Acción para cancelar la impresión actual en Klipper (Moonraker)"""

import requests

from elGarrobo.accionesOOP.accion import accion, propiedadAccion
from elGarrobo.accionesOOP.accionNotificacion import accionNotificacion
from elGarrobo.miLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


class accionCancelarKlipper(accion):
    """Cancela la impresión actual en Klipper usando la API de Moonraker"""

    nombre = "Cancelar Klipper"
    comando = "cancelar_klipper"
    descripcion = "Cancela la impresión actual en Klipper (Moonraker)"

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

        self.funcion = self.cancelarTrabajo

    def notificar(self, texto: str) -> None:
        notificación = accionNotificacion()
        notificación.configurar({"texto": texto})
        notificación.ejecutar()

    def cancelarTrabajo(self):
        """Cancela la impresión en curso"""
        base_url = str(self.obtenerValor("url")).strip().rstrip("/")
        token = self.obtenerValor("token")
        headers = {"X-Api-Key": str(token).strip()} if token else {}

        try:
            response = requests.post(f"{base_url}/printer/print/cancel", headers=headers, timeout=10)
            response.raise_for_status()

            Logger.info(f"Klipper[OK] Cancelación enviada a {base_url}")
            self.notificar(f"Klipper[OK] Cancelación enviada a {base_url}")

        except requests.RequestException as error:
            detalle = (getattr(error.response, "text", "") or str(error)).strip()[:300]
            Logger.error(f"Klipper[Error] {base_url}: {detalle}")
            self.notificar(f"Klipper[Error] {base_url}: {detalle}")
