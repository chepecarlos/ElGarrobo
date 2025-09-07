"""Lista de Acciones."""

from .archivos import escribirArchivo, escribirValor, escribirValores, leerValor

# from .emular_teclado import CopiarTexto, comandoPegar, comandoPortapapeles
from .emular_teclado import comandoPegar, comandoPortapapeles
from .operaciones import OperacionConstrain, operacionAsignar, operacionConcatenar
from .sonidos import PararReproducion, Reproducir
from .textbox import VentanaTexto
from .textovoz import TextoVoz

# from .emular_raton import precionarRaton
# from .ventanas import cerrarVentana  # mostarVentana


def CargarAcciones():
    """
    Carga las acciones en una dic con nombre de accion y funcion asociada.
    """

    return {
        # "delay": delay,
        "contrain": OperacionConstrain,
        # "mqtt": mensajeMQTT,
        # OS
        # "os": accionOS,
        # "notificacion": Notificacion,
        # Precionas teclas
        # "teclas": comandoTeclas,
        # "escribir": comandoEscribir,
        "pegar": comandoPegar,
        # "copiar": CopiarTexto,
        "portapapeles": comandoPortapapeles,
        # "raton": precionarRaton,
        # Audio
        # "reproducion": Reproducir,
        # "detener_reproducion": PararReproducion,
        "textovoz": TextoVoz,
        # Archivos
        "leer_valor": leerValor,
        "escribir_valor": escribirValor,
        "escribir_valores": escribirValores,
        "escribir_archivo": escribirArchivo,
        # Manejo de Ventanas
        # "cerrar_ventana": cerrarVentana,
        # "mostrar_ventana": mostarVentana,
        # Input
        "ventana_texto": VentanaTexto,
        # Operacion
        "concatenar": operacionConcatenar,
        "asignar": operacionAsignar,
    }
