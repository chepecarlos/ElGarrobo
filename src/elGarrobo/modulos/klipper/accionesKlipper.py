"""Acciones para controlar impresiones en Klipper (Moonraker)"""

import requests

from elGarrobo.accionesOOP.accion import propiedadAccion
from elGarrobo.modulos.modulo import accionImpresora


def conexionKlipper() -> list[propiedadAccion]:
    """URL y token, solo si la impresora no está en el módulo"""
    return [
        propiedadAccion(
            nombre="URL",
            atributo="url",
            tipo=[str],
            descripcion="URL de Moonraker, si la impresora no está en el módulo",
            ejemplo="http://192.168.1.10:7125",
        ),
        propiedadAccion(
            nombre="Token",
            atributo="token",
            tipo=[str],
            descripcion="API key de Moonraker (si tiene autenticación activada)",
            ejemplo="1234567890abcdef",
        ),
    ]


class accionKlipper(accionImpresora):
    """Acción sobre Moonraker: URL y headers de la impresora elegida"""

    def __init__(self) -> None:
        super().__init__(conexionKlipper(), "Impresora del módulo Klipper, toma su URL")

    def moonraker(self) -> tuple[str, dict, str] | None:
        """(url base, headers, nombre para los avisos) o None si falta la URL"""
        valores = self.conexion("url")
        if valores is None:
            return None
        base_url = str(valores["url"]).strip().rstrip("/")
        headers = {"X-Api-Key": str(valores["token"]).strip()} if valores["token"] else {}
        return base_url, headers, valores["impresora"] or base_url


class accionCancelarKlipper(accionKlipper):
    """Cancela la impresión actual en Klipper usando la API de Moonraker"""

    nombre = "Cancelar Klipper"
    comando = "cancelar_klipper"
    descripcion = "Cancela la impresión actual en Klipper (Moonraker), de una impresora del módulo o con URL"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = self.cancelarTrabajo

    def cancelarTrabajo(self):
        """Cancela la impresión en curso"""
        datos = self.moonraker()
        if datos is None:
            return
        base_url, headers, destino = datos

        try:
            response = requests.post(f"{base_url}/printer/print/cancel", headers=headers, timeout=10)
            response.raise_for_status()
            self.notificar(f"Klipper[OK] Cancelación enviada a {destino}")

        except requests.RequestException as error:
            detalle = (getattr(error.response, "text", "") or str(error)).strip()[:300]
            self.notificar(f"Klipper[Error] {destino}: {detalle}")


class accionReimprimirKlipper(accionKlipper):
    """Reimprime el último trabajo en Klipper usando la API de Moonraker"""

    nombre = "Reimprimir Klipper"
    comando = "reimprimir_klipper"
    descripcion = "Reimprime el último trabajo en Klipper (Moonraker), de una impresora del módulo o con URL"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = self.reimprimirTrabajo

    def reimprimirTrabajo(self):
        """Busca el último archivo impreso en el historial y lo vuelve a iniciar"""
        datos = self.moonraker()
        if datos is None:
            return
        base_url, headers, destino = datos

        try:
            response = requests.get(f"{base_url}/server/history/list", headers=headers, params={"limit": 1}, timeout=10)
            response.raise_for_status()
            trabajos = response.json().get("result", {}).get("jobs", [])
            if not trabajos:
                self.notificar(f"Klipper[Error] No hay trabajos en el historial de {destino}")
                return

            archivo = trabajos[0]["filename"]
            response = requests.post(f"{base_url}/printer/print/start", headers=headers, params={"filename": archivo}, timeout=10)
            response.raise_for_status()
            self.notificar(f"Klipper[OK] Reimpresión de {archivo} enviada a {destino}")

        except requests.RequestException as error:
            detalle = (getattr(error.response, "text", "") or str(error)).strip()[:300]
            self.notificar(f"Klipper[Error] {destino}: {detalle}")
