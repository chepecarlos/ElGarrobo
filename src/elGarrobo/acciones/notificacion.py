"""Acciones de notificaciones de Escritorio."""
# https://github.com/ms7m/notify-py
from elGarrobo.miLibrerias import ObtenerFolderConfig, UnirPath
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
    texto = opciones.get("texto")
    titulo = opciones.get("titulo","ElGatoALSW")
    icono = opciones.get('icono')
    iconoRelativo = opciones.get('icono_relativo', False)

    if texto is not None:

        noti = Notify()
        noti.message = texto
        noti.application_name = "ElGatoALSW"
        noti.title = titulo

        if icono is not None:
            if iconoRelativo:
                icono = UnirPath(ObtenerFolderConfig, icono)
            noti.icon = icono
        noti.send()
        # TODO: que hace block=False
