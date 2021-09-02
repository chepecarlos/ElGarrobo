from .notificacion import Notificacion
from .delay import Delay
from .emular_teclado import ComandoTeclas, ComandoEscribir, ComandoPegar, CopiarTexto
from .sonidos import PararReproducion, Reproducir
from .accion_os import AccionOS
from .Archivos import LeerValor, EscrivirValor
from .operaciones import OperacionConstrain


def CargarAcciones():

    return {
        'delay': Delay,
        'notification': Notificacion,
        'teclas': ComandoTeclas,
        "escribir": ComandoEscribir,
        "pegar": ComandoPegar,
        "copiar": CopiarTexto,
        "reproducion": Reproducir,
        "parar_reproducion": PararReproducion,
        "os": AccionOS,
        "leer_valor": LeerValor,
        "escrivir_valor": EscrivirValor,
        "contrain": OperacionConstrain
    }
