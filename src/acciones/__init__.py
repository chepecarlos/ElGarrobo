"""Lista de Acciones."""

from .accion_os import AccionOS
from .archivos import EscrivirValor, LeerValor
from .delay import Delay
from .emular_teclado import ComandoEscribir, ComandoPegar, ComandoTeclas, CopiarTexto
from .mqtt import MensajeMQTT
from .notificacion import Notificacion
from .operaciones import OperacionConstrain
from .sonidos import PararReproducion, Reproducir
from .textbox import VentanaTexto
from .textovoz import TextoVoz
from .ventanas import CerrarVentana, MostarVentana


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
        # Input
        "ventana_texto": VentanaTexto,
    }
