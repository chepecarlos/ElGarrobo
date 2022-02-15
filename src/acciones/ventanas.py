"""Acciones de manejo de ventanas de escritorio."""
# https://github.com/jordansissel/xdotool
# sudo apt install xdotool
from MiLibrerias import ConfigurarLogging

from .accion_os import accionOS

logger = ConfigurarLogging(__name__)


def cerrarVentana(opciones):
    """
    Activa el cerrar ventanas con el cursor
    """
    logger.info("Seleciona programa a carrar")
    accionOS({"comando": "xdotool selectwindow windowclose"})


def mostarVentana(opciones):
    """
    Cambia a ventana que contenga el titulo

    titulo -> stl
        titulo a buscar
    """
    titulo = None
    if "titulo" in opciones:
        titulo = opciones["titulo"]

    if titulo is None:
        return

    comando = f'xdotool search --onlyvisible "{titulo}" windowactivate'
    logger.info(f"Buscando ventana[{titulo}]")
    accionOS({"comando": comando})
    # Agregar mensaje si no esta la venta


# TODO: Marcar Ventana favorita
# xdotool selectwindow
