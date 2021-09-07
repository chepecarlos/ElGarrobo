# https://github.com/ms7m/notify-py
from notifypy import Notify
from MiLibrerias import UnirPath, ObtenerFolderConfig

def Notificacion(Opciones):
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
    if 'texto' in Opciones:
        Texto = Opciones['texto']

        Noti = Notify()
        Noti.message = Texto

        if 'titulo' in Opciones:
            Noti.title = Opciones['titulo']
        else:
            Noti.title = "ElGatoALSW"

        if 'icono' in Opciones:
            DirecionIcono = Opciones['icono']
            if 'icono_relativo' in Opciones:
                if Opciones['icono_relativo']:
                    DirecionIcono = UnirPath(ObtenerFolderConfig, DirecionIcono)

            Noti.icon = DirecionIcono
        Noti.send()
        # TODO: que hace block=False
    



