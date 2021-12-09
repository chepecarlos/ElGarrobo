from .notificacion import Notificacion
from .delay import Delay
from .emular_teclado import ComandoTeclas, ComandoEscribir, ComandoPegar, CopiarTexto
from .sonidos import PararReproducion, Reproducir
from .accion_os import AccionOS
from .archivos import LeerValor, EscrivirValor
from .operaciones import OperacionConstrain
from .ventanas import CerrarVentana, MostarVentana
from .mqtt import MensajeMQTT
from .textovoz import TextoVoz

def CargarAcciones():
    """
    Carga las acciones en una dic con nombre de accion y funcion asociada.
    """

    return {
        "delay": Delay,
        "contrain": OperacionConstrain,
        "mqtt": MensajeMQTT,
        # OS
        "os": AccionOS,
        "notificacion": Notificacion,
        # Precionas teclas
        "teclas": ComandoTeclas,
        "escribir": ComandoEscribir,
        "pegar": ComandoPegar,
        "copiar": CopiarTexto,
        # Audio
        "reproducion": Reproducir,
        "detener_reproducion": PararReproducion,
        "textovoz": TextoVoz,
        # Archivos
        "leer_valor": LeerValor,
        "escrivir_valor": EscrivirValor,
        # Manejo de Ventanas
        "cerrar_ventana": CerrarVentana,
        "mostar_ventana": MostarVentana,
    }
