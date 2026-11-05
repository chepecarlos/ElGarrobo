"""Acciones para controlar impresiones en Octoprint"""

import requests

from elGarrobo.accionesOOP.accion import propiedadAccion
from elGarrobo.modulos.modulo import accionImpresora


def conexionOctoprint() -> list[propiedadAccion]:
    """URL y token, solo si la impresora no está en el módulo"""
    return [
        propiedadAccion(
            nombre="URL",
            atributo="url",
            tipo=[str],
            descripcion="URL de Octoprint, si la impresora no está en el módulo",
            ejemplo="http://octoprint.local",
        ),
        propiedadAccion(
            nombre="Token",
            atributo="token",
            tipo=[str],
            descripcion="API key de Octoprint, si la impresora no está en el módulo",
            ejemplo="1234567890abcdef",
        ),
    ]


class accionOctoprint(accionImpresora):
    """Manda un comando a /api/job de Octoprint"""

    def __init__(self) -> None:
        super().__init__(conexionOctoprint(), "Impresora del módulo Octoprint, toma su URL y token")

    def enviarComando(self, comandos: list[str], texto: str) -> None:
        """Prueba los comandos en orden mientras Octoprint responda 409 (no aplica en el estado actual)"""
        valores = self.conexion("url", "token")
        if valores is None:
            return
        base_url = str(valores["url"]).strip().rstrip("/")
        # Si ya llega /api/job no lo duplicamos.
        endpoint = base_url if base_url.endswith("/api/job") else f"{base_url}/api/job"
        headers = {"X-Api-Key": str(valores["token"]).strip(), "Content-Type": "application/json"}
        destino = valores["impresora"] or endpoint

        try:
            for comando in comandos:
                response = requests.post(endpoint, headers=headers, json={"command": comando}, timeout=10)
                if response.status_code != 409:
                    break

            if response.status_code in [200, 204]:
                self.notificar(f"Octoprint[OK] {texto} en {destino}")
                return

            detalle = (response.text or "").strip()[:300]
            self.notificar(f"Octoprint[Error] HTTP {response.status_code} en {destino}. Respuesta: {detalle}")

        except requests.RequestException as error:
            self.notificar(f"Octoprint[Error] No se pudo conectar a {destino}: {error}")


class accionCancelarOctoprint(accionOctoprint):
    """Cancela una impresión en Octoprint"""

    nombre = "Cancelar Octoprint"
    comando = "cancelar_octoprint"
    descripcion = "Cancela la impresión en Octoprint, de una impresora del módulo o con URL y token"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = lambda: self.enviarComando(["cancel"], "Impresión cancelada")


class accionReimprimirOctoprint(accionOctoprint):
    """Reimprime un trabajo en Octoprint"""

    nombre = "Reimprimir Octoprint"
    comando = "reimprimir_octoprint"
    descripcion = "Reimprime el último trabajo en Octoprint, de una impresora del módulo o con URL y token"

    def __init__(self) -> None:
        super().__init__()
        # 'restart' reinicia el archivo cargado; si no aplica (409) se prueba 'start'
        self.funcion = lambda: self.enviarComando(["restart", "start"], "Reimpresión enviada")
