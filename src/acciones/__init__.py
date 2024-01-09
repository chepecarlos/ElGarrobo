"""Lista de Acciones."""

from .accion_os import accionOS
from .archivos import escribirValor, escribirValores, leerValor
from .delay import delay
from .emular_raton import precionarRaton
from .emular_teclado import CopiarTexto, comandoEscribir, comandoPegar, comandoPortapapeles, comandoTeclas
from .mqtt import mensajeMQTT
from .notificacion import Notificacion
from .operaciones import OperacionConstrain, operacionAsignar, operacionConcatenar
from .sonidos import PararReproducion, Reproducir
from .textbox import VentanaTexto
from .textovoz import TextoVoz
from .ventanas import cerrarVentana, mostarVentana


def CargarAcciones():
    """
    Carga las acciones en una dic con nombre de accion y funcion asociada.
    """

    return {
        # "delay": delay,
        "contrain": OperacionConstrain,
        "mqtt": mensajeMQTT,
        # OS
        # "os": accionOS,
        # "notificacion": Notificacion,
        # Precionas teclas
        "teclas": comandoTeclas,
        "escribir": comandoEscribir,
        "pegar": comandoPegar,
        "copiar": CopiarTexto,
        "portapapeles": comandoPortapapeles,
        "raton": precionarRaton,
        # Audio
        "reproducion": Reproducir,
        "detener_reproducion": PararReproducion,
        "textovoz": TextoVoz,
        # Archivos
        "leer_valor": leerValor,
        "escribir_valor": escribirValor,
        "escribir_valores": escribirValores,
        # Manejo de Ventanas
        "cerrar_ventana": cerrarVentana,
        "mostrar_ventana": mostarVentana,
        # Input
        "ventana_texto": VentanaTexto,
        # Operacion
        "concatenar": operacionConcatenar,
        "asignar": operacionAsignar,
    }
