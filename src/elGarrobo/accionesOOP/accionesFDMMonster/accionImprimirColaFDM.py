"""Acción para mandar a imprimir el siguiente trabajo de la cola en FDM Monster"""

import requests

from elGarrobo.accionesOOP.accion import accion, propiedadAccion
from elGarrobo.accionesOOP.accionNotificacion import accionNotificacion
from elGarrobo.miLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


class accionImprimirColaFDM(accion):
    """Manda a imprimir el siguiente trabajo en la cola de una impresora de FDM Monster"""

    nombre = "Imprimir cola FDM Monster"
    comando = "imprimir_cola_fdm"
    descripcion = "Manda a imprimir el siguiente trabajo en la cola de una impresora de FDM Monster"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.agregarPropiedad(
            propiedadAccion(
                nombre="URL",
                atributo="url",
                tipo=[str],
                obligatorio=True,
                descripcion="URL de FDM Monster",
                ejemplo="http://192.168.50.200:4000",
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Usuario",
                atributo="usuario",
                tipo=[str],
                obligatorio=True,
                descripcion="Usuario de FDM Monster",
                ejemplo="admin",
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Clave",
                atributo="clave",
                tipo=[str],
                obligatorio=True,
                descripcion="Contraseña de FDM Monster",
                ejemplo="1234",
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Impresora",
                atributo="impresora",
                tipo=[str],
                obligatorio=True,
                descripcion="Nombre de la impresora en FDM Monster",
                ejemplo="MK4s",
            )
        )

        self.funcion = self.imprimirSiguiente

    def notificar(self, texto: str) -> None:
        notificación = accionNotificacion()
        notificación.configurar({"texto": texto})
        notificación.ejecutar()

    def imprimirSiguiente(self):
        """Busca la impresora por nombre y manda el siguiente trabajo de su cola"""
        api = f"{str(self.obtenerValor('url')).strip().rstrip('/')}/api/v2"
        nombre = str(self.obtenerValor("impresora")).strip()

        try:
            login = requests.post(
                f"{api}/auth/login",
                json={"username": self.obtenerValor("usuario"), "password": self.obtenerValor("clave")},
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
            Logger.info(f"FDM[OK] {nombre} imprimiendo {trabajo['fileName']}")
            self.notificar(f"FDM {nombre} imprimiendo: {trabajo['fileName']}")

        except requests.RequestException as error:
            detalle = (getattr(error.response, "text", "") or str(error)).strip()[:300]
            Logger.error(f"FDM[Error] {nombre}: {detalle}")
            self.notificar(f"FDM[Error] {nombre}: {detalle}")
