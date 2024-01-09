from .accionBase import accionBase

from MiLibrerias import ConfigurarLogging
from MiLibrerias import ObtenerFolderConfig, UnirPath
from notifypy import Notify

Logger = ConfigurarLogging(__name__)


class accionNotificacion(accionBase):
    def __init__(self) -> None:
        nombre = "Notificacion"
        comando = "notificacion"
        descripcion = "Muestra un mensaje de escritorio"
        super().__init__(nombre, comando, descripcion)

        propiedadTexto = {
            "nombre": "texto",
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
        # TODO: que hace block=False
