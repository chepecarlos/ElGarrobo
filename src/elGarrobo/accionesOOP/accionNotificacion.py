"""Muestra un mensaje de escritorio"""

from notifypy import Notify

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerFolderConfig, UnirPath

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionNotificacion(accionBase):
    """Muestra un mensaje de escritorio"""

    nombre = "Notificacion"
    comando = "notificacion"
    descripcion = "Muestra un mensaje de escritorio"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadTexto = {
            "nombre": "Texto",
            "tipo": str,
            "obligatorio": True,
            "atributo": "texto",
            "descripcion": "texto a mostrar",
            "ejemplo": "mensaje importante",
        }

        propiedadTitulo = {
            "nombre": "titulo",
            "tipo": str,
            "obligatorio": False,
            "atributo": "titulo",
            "descripcion": "titulo del mensaje",
            "ejemplo": "Nombre de la app",
            "defecto": "LaIguanaApp",
        }

        propiedadIcono = {
            "nombre": "icono",
            "tipo": str,
            "obligatorio": False,
            "atributo": "icono",
            "descripcion": "icono a mostrar en el mensaje",
            "ejemplo": "/home/logo.png",
        }

        self.agregarPropiedad(propiedadTexto)
        self.agregarPropiedad(propiedadTitulo)
        self.agregarPropiedad(propiedadIcono)

        self.funcion = self.ejecutrarNotificacion

    def ejecutrarNotificacion(self):
        """Ejecuta comando en terminal"""
        texto = self.obtenerValor("texto")
        titulo = self.obtenerValor("titulo")
        icono = self.obtenerValor("icono")

        comando = self.obtenerValor("comando")

        noti = Notify()
        noti.message = texto
        noti.title = titulo
        noti.application_name = "ElGatoALSW"

        if icono is not None:
            # TODO: agregar icono relativo
            # if iconoRelativo:
            #     icono = UnirPath(ObtenerFolderConfig, icono)
            noti.icon = icono
        noti.send()
        Logger.info(f"Notificación[{texto}]")
        # TODO: que hace block=False
