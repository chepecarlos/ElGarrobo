"""Lista de Acciones."""

from .accionAbirGUI import accionAbirGUI
from .accionCambiarPagina import (
    accionActualizarPagina,
    accionAnteriorPagina,
    accionSiquientePagina,
)
from .accionControl import accionControl
from .accionDelay import accionDelay
from .accionEntrarFolder import accionEntrarFolder
from .accionFolder import accionFolder
from .accionMQTT import accionMQTT
from .accionNavegador import accionNavegador
from .accionNotificacion import accionNotificacion
from .accionOS import accionOS
from .accionRegresarFolder import accionRegresarFolder
from .accionSalir import accionSalir
from .accionTeclas import accionTeclas
from .accionTelegram import accionTelegram


def cargarAcciones() -> dict[str:]:
    """
    Carga las acciones en una dic con nombre de accion y función asociada.
    """

    return {
        "abir_gui": accionAbirGUI,
        "anterior_pagina": accionAnteriorPagina,
        "siquiente_pagina": accionSiquientePagina,
        "actualizar_pagina": accionActualizarPagina,
        "control": accionControl,
        "delay": accionDelay,
        "entrar_folder": accionEntrarFolder,
        "folder": accionFolder,
        "mqtt": accionMQTT,
        "navegador": accionNavegador,
        "notificacion": accionNotificacion,
        "os": accionOS,
        "regresar_folder": accionRegresarFolder,
        "salir": accionSalir,
        "teclas": accionTeclas,
        "telegram": accionTelegram,
    }
