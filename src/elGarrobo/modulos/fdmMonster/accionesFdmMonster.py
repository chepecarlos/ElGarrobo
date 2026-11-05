"""Acciones para controlar la cola de impresión en FDM Monster"""

import requests

from elGarrobo.accionesOOP.accion import propiedadAccion
from elGarrobo.modulos.modulo import accionImpresora


class accionImprimirColaFDM(accionImpresora):
    """Manda a imprimir el siguiente trabajo en la cola de una impresora de FDM Monster"""

    nombre = "Imprimir cola FDM Monster"
    comando = "imprimir_cola_fdm"
    descripcion = "Manda a imprimir el siguiente trabajo en la cola de una impresora de FDM Monster"

    def __init__(self) -> None:
        conexion = [
            propiedadAccion(
                nombre="URL",
                atributo="url",
                tipo=[str],
                descripcion="URL de FDM Monster, si no se usa el servidor del módulo",
                ejemplo="http://192.168.50.200:4000",
            ),
            propiedadAccion(nombre="Usuario", atributo="usuario", tipo=[str], descripcion="Usuario de FDM Monster", ejemplo="admin"),
            propiedadAccion(nombre="Clave", atributo="clave", tipo=[str], descripcion="Contraseña de FDM Monster", ejemplo="1234"),
        ]
        super().__init__(conexion, "Nombre de la impresora en el servidor de FDM Monster del módulo")
        self.funcion = self.imprimirSiguiente

    def nombresImpresoras(self) -> list[str]:
        # Las impresoras están en el servidor, el módulo guarda las que vio en la última consulta
        return list(getattr(self.modulo, "valoresDatos", {}).get("impresora", []))

    def datosModulo(self, nombre: str) -> dict:
        # Un solo servidor para todas las impresoras: url, usuario y clave del módulo
        return getattr(self.modulo, "config", None) or {}

    def imprimirSiguiente(self):
        """Busca la impresora por nombre y manda el siguiente trabajo de su cola"""
        valores = self.conexion("impresora", "url", "usuario")
        if valores is None:
            return
        api = f"{str(valores['url']).strip().rstrip('/')}/api/v2"
        nombre = valores["impresora"]

        try:
            login = requests.post(
                f"{api}/auth/login",
                json={"username": valores["usuario"], "password": valores["clave"]},
                timeout=10,
            )
            login.raise_for_status()
            sesion = requests.Session()
            sesion.headers["Authorization"] = f"Bearer {login.json()['token']}"

            impresoras = sesion.get(f"{api}/printer/", timeout=10).json()
            impresora = next((i for i in impresoras if i["name"].lower() == nombre.lower()), None)
            if impresora is None:
                self.notificar(f"FDM[Error] No existe la impresora {nombre}")
                return
            nombre = impresora["name"]

            trabajo = sesion.get(f"{api}/print-queue/{impresora['id']}/next", timeout=10).json()["nextJob"]
            if trabajo is None:
                self.notificar(f"FDM {nombre}: no hay nada en cola")
                return

            sesion.post(f"{api}/print-queue/{impresora['id']}/submit/{trabajo['id']}", timeout=30).raise_for_status()
            self.notificar(f"FDM {nombre} imprimiendo: {trabajo['fileName']}")

        except requests.RequestException as error:
            detalle = (getattr(error.response, "text", "") or str(error)).strip()[:300]
            self.notificar(f"FDM[Error] {nombre}: {detalle}")
