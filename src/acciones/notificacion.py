"""Acciones de Notificaciones de Escritorio."""
# https://github.com/ms7m/notify-py
from MiLibrerias import ObtenerFolderConfig, UnirPath
from notifypy import Notify


def Notificacion(opciones):
    """
    Muestra una notificacion de Escritorio

    texto -> str
        Texto de la notificacion
    titulo -> str
        Titulo de la notificacion
    icono -> str
        direcion del icono
    icono_relativo -> bool
        direcion del icono dentro de folder config
    """
    if "texto" in opciones:
        Texto = opciones["texto"]

        Noti = Notify()
        Noti.message = Texto
        Noti.application_name = "ElGatoALSW"

        if "titulo" in opciones:
            Noti.title = opciones["titulo"]
        else:
            Noti.title = "ElGatoALSW"

        # TODO: Iconos relativo
        if "icono" in opciones:
            DirecionIcono = opciones["icono"]
            if "icono_relativo" in opciones:
                if opciones["icono_relativo"]:
                    DirecionIcono = UnirPath(ObtenerFolderConfig, DirecionIcono)

            Noti.icon = DirecionIcono
        Noti.send()
        # TODO: que hace block=False
