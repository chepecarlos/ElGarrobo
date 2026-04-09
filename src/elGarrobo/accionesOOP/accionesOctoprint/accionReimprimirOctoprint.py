"""Acción para reimprimir un trabajo en Octoprint"""

import requests

from elGarrobo.accionesOOP.accion import accion, propiedadAccion
from elGarrobo.accionesOOP.accionNotificacion import accionNotificacion
from elGarrobo.miLibrerias import ConfigurarLogging

# from .heramientas.propiedadAccion import propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionReimprimirOctoprint(accion):
    """Reimprime un trabajo en Octoprint"""

    nombre = "Reimprimir Octoprint"
    comando = "reimprimir_octoprint"
    descripcion = "Reimprime un trabajo en Octoprint"

    esperarSegundos: int | str = 0

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadURL = propiedadAccion(
            nombre="URL",
            atributo="url",
            tipo=[str],
            obligatorio=True,
            descripcion="URL del trabajo a reimprimir",
            ejemplo="http://octoprint.local",
        )

        propiedadToken = propiedadAccion(
            nombre="Token",
            atributo="token",
            tipo=[str],
            obligatorio=True,
            descripcion="Token de acceso a Octoprint",
            ejemplo="1234567890abcdef",
        )

        self.agregarPropiedad(propiedadURL)
        self.agregarPropiedad(propiedadToken)

        self.funcion = self.reimprimirTrabajo

    def reimprimirTrabajo(self):
        """Reimprime un trabajo en Octoprint"""
        url = str(self.obtenerValor("url")).strip()
        token = str(self.obtenerValor("token")).strip()

        # Si ya llega /api/job no lo duplicamos.
        base_url = url.rstrip("/")
        endpoint = base_url if base_url.endswith("/api/job") else f"{base_url}/api/job"

        headers = {"X-Api-Key": token, "Content-Type": "application/json"}
        # El comando 'restart' reinicia el archivo cargado; si no aplica, hacemos fallback a 'start'.
        data = {"command": "restart"}

        try:
            response = requests.post(endpoint, headers=headers, json=data, timeout=10)

            if response.status_code in [200, 204]:
                Logger.info(f"Octoprint[OK] Reimpresión enviada a {endpoint}")
                notificación = accionNotificacion()
                notificación.configurar({"texto": f"Octoprint[OK] Reimpresión enviada a {endpoint}"})
                notificación.ejecutar()
                return

            if response.status_code == 409:
                data = {"command": "start"}
                response = requests.post(endpoint, headers=headers, json=data, timeout=10)
                if response.status_code in [200, 204]:
                    Logger.info(f"Octoprint[OK] Se inició impresión con fallback 'start' en {endpoint}")

                    notificación = accionNotificacion()
                    notificación.configurar({"texto": f"Octoprint[OK] Reimpresión enviada a {endpoint}"})
                    notificación.ejecutar()
                    return

            detalle = (response.text or "").strip()
            if len(detalle) > 300:
                detalle = f"{detalle[:300]}..."
            Logger.error(f"Octoprint[Error] HTTP {response.status_code} en {endpoint}. Respuesta: {detalle}")

            notificación = accionNotificacion()
            notificación.configurar({"texto": f"Octoprint[Error] HTTP {response.status_code} en {endpoint}. Respuesta: {detalle}"})
            notificación.ejecutar()

        except requests.RequestException as error:
            Logger.error(f"Octoprint[Error] No se pudo conectar a {endpoint}: {error}")

            notificación = accionNotificacion()
            notificación.configurar({"texto": f"Octoprint[Error] No se pudo conectar a {endpoint}: {error}"})
            notificación.ejecutar()
