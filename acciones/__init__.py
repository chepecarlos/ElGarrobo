from .notificacion import Notificacion
from .delay import Delay
from .emular_teclado import ComandoTeclas, ComandoEscribir, ComandoPegar, CopiarTexto
from .sonidos import PararReproducion, Reproducir
from .accion_os import AccionOS
from .Archivos import LeerValor, EscrivirValor
from .operaciones import OperacionConstrain
from .Ventanas import CerrarVentana, MostarVentana


def CargarAcciones():

    return {
        'delay': Delay,
        "contrain": OperacionConstrain,
        # OS
        "os": AccionOS,
        'notification': Notificacion,
        # Precionas teclas
        'teclas': ComandoTeclas,
        "escribir": ComandoEscribir,
        "pegar": ComandoPegar,
        "copiar": CopiarTexto,
        # Audio
        "reproducion": Reproducir,
        "parar_reproducion": PararReproducion,
        # Archivos
        "leer_valor": LeerValor,
        "escrivir_valor": EscrivirValor,
        # Manejo de Ventanas
        "cerrar_ventana": CerrarVentana,
        "mostar_ventana": MostarVentana
    }
