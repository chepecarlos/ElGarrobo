# https://github.com/jordansissel/xdotool
# sudo apt install xdotool
from .accion_os import AccionOS
from MiLibrerias import ConfigurarLogging
Logger = ConfigurarLogging(__name__)


def CerrarVentana(Opciones):
    """
        Activa el cerrar ventanas con el cursor
    """
    Logger.info("Seleciona programa a carrar")
    AccionOS({"comando": "xdotool selectwindow windowclose"})


def MostarVentana(Opciones):
    """
        Cambia a ventana que contenga el titulo

        titulo -> stl
            titulo a buscar 
    """
    Titulo = ""
    if 'titulo' in Opciones:
        Titulo = Opciones['titulo']
    Comando = f'xdotool search --onlyvisible "{Titulo}" windowactivate'
    Logger.info(f"Buscando ventana[{Titulo}]")
    print(Comando)
    AccionOS({"comando": Comando})
    # Agregar mensaje si no esta la venta

# TODO: Marcar Ventana favorita
# xdotool selectwindow
