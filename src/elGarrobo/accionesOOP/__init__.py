"""
## Acción Base
- Clase que se herencia todas las funciones: [AccionBase](./accionesOOP/accionBase)

## Lista de Acciones 
- Abri Interface web: [accionAbirGUI](./accionesOOP/accionAbirGUI)
- Buscar Ventana: [accionBuscarVentana](./accionesOOP/accionBuscarVentana)
- Siguiente pagina de StreamDeck: [accionAnteriorPagina](./accionesOOP/accionAnteriorPagina)
- [accionSiquientePagina](./accionesOOP/accionSiquientePagina)
- [accionActualizarPagina](./accionesOOP/accionActualizarPagina)
- [accionControl](./accionesOOP/accionControl)
- [accionDelay](./accionesOOP/accionDelay)
- [accionEntrarFolder](./accionesOOP/accionEntrarFolder)
- [accionEscribirTexto](./accionesOOP/accionEscribirTexto)
- [accionFolder](./accionesOOP/accionFolder)
- [accionMQTT](./accionesOOP/accionMQTT)
- [accionNavegador](./accionesOOP/accionNavegador)
- [accionNotificacion](./accionesOOP/accionNotificacion)
- [accionOS](./accionesOOP/accionOS)
-  [accionRegresarFolder](./accionesOOP/accionRegresarFolder)
- Cierra el programa: [accionSalir](./accionesOOP/accionSalir)
- Preciosa una combinación de teclas: [accionTeclas](./accionesOOP/accionTeclas)
- Envía mensaje por telegram: [accionTelegram](./accionesOOP/accionTelegram)
"""

from .accionAbirGUI import accionAbirGUI
from .accionBuscarVentana import accionBuscarVentana
from .accionCambiarPagina import (
    accionActualizarPagina,
    accionAnteriorPagina,
    accionSiquientePagina,
)
from .accionControl import accionControl
from .accionDelay import accionDelay
from .accionEntrarFolder import accionEntrarFolder
from .accionEscribirTexto import accionEscribirTexto
from .accionFolder import accionFolder
from .accionMQTT import accionMQTT
from .accionNavegador import accionNavegador
from .accionNotificacion import accionNotificacion
from .accionOS import accionOS
from .accionRecargarFolder import accionRecargarFolder
from .accionRegresarFolder import accionRegresarFolder
from .accionSalir import accionSalir
from .accionTeclas import accionTeclas
from .accionTelegram import accionTelegram


def cargarClasesAcciones() -> dict[str:]:
    """
    Carga las acciones en una dic con nombre de accion y función asociada.
    """

    return {
        "abir_gui": accionAbirGUI,
        "mostrar_ventana": accionBuscarVentana,
        "anterior_pagina": accionAnteriorPagina,
        "siquiente_pagina": accionSiquientePagina,
        "actualizar_pagina": accionActualizarPagina,
        "control": accionControl,
        "delay": accionDelay,
        "entrar_folder": accionEntrarFolder,
        "escribir": accionEscribirTexto,
        "folder": accionFolder,
        "mqtt": accionMQTT,
        "navegador": accionNavegador,
        "notificacion": accionNotificacion,
        "os": accionOS,
        "reiniciar_data": accionRecargarFolder,
        "regresar_folder": accionRegresarFolder,
        "salir": accionSalir,
        "teclas": accionTeclas,
        "telegram": accionTelegram,
    }
