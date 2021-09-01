from .notificacion import Notificacion
from .delay import Delay
from .emular_teclado import ComandoTeclas, ComandoEscribir, ComandoPegar
from .Sonidos import PararReproducion, Reproducir
from .accion_os import AccionOS
from .Archivos import LeerValor, EscrivirValor


def CargarAcciones():

    return {
        'delay': Delay,
        'notification': Notificacion,
        'comando_teclas': ComandoTeclas,
        "comando_escribir": ComandoEscribir,
        "comando_pegar": ComandoPegar,
        "reproducion": Reproducir,
        "parar_reproducion": PararReproducion,
        "os": AccionOS,
        "leer_valor": LeerValor,
        "escrivir_valor": EscrivirValor
    }
