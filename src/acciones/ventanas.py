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
    logger.info("Selecciona programa a cerrar")
    accionOS({"comando": "xdotool selectwindow windowclose"})


def mostarVentana(opciones):
    """
    Cambia a ventana que contenga el titulo

    titulo -> stl
        titulo a buscar
    """
    titulo = opciones.get("titulo")

    if titulo is not None:
        comando = f'xdotool search --onlyvisible "{titulo}" windowactivate'
        logger.info(f"Buscando ventana[{titulo}]")
        accionOS({"comando": comando})
        # Agregar mensaje si no esta la venta


# TODO: Marcar Ventana favorita
# xdotool selectwindow
