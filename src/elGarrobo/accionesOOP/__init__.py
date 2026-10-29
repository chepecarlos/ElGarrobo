"""
## Acción Base
- Clase que se herencia todas las acciones: [accion](./accionesOOP/accion)

# Lista de Acciones
- Preciosa una combinación de teclas: [accionTeclas](./accionesOOP/accionTeclas)
- Buscar Ventana: [accionBuscarVentana](./accionesOOP/accionBuscarVentana)
- Envía mensaje por telegram: [accionTelegram](./accionesOOP/accionTelegram)
- Envía mensaje por MQTT: [accionMQTT](./accionesOOP/accionMQTT)
- Hace una espera: [accionDelay](./accionesOOP/accionDelay)
- Escribe en un archivo: [accionEscribirTexto](./accionesOOP/accionEscribirTexto)
- Abre una pagina web: [accionNavegador](./accionesOOP/accionNavegador)
- Cierra la ventana usando el cursor: [accionCerrarVentana](./accionesOOP/accionCerrarVentana)
- Copia texto al portapapeles: [accionCopiarPapelera](./accionesOOP/accionCopiarPapelera)
- Pega texto usando el portapapeles: [accionPegarTexto](./accionesOOP/accionCopiarPapelera)
- Manda una notificación al escritorio: [accionNotificacion](./accionesOOP/accionNotificacion)
- Ejecuta la comando en terminal: [accionOS](./accionesOOP/accionOS)
- Controla la PC a distancia: [accionControl](./accionesOOP/accionControl)
- Reproduce una pista de audio: [accionReproducir](./accionesOOP/accionSonidos)
- Para todas las reproducciones: [accionPararReproducciones](./accionesOOP/accionSonidos)
- Ejecuta accion preciosa y otra se suelta: [accionPresionar](./accionesOOP/accionPresionar)
- Escribir archivo[accionEscribirArchivo](./accionesOOP/accionArchivo)
- Lee un valor de un archivo[accionLeerValor](./accionesOOP/accionArchivo)
- Muestra una lista de tareas emergente: [accionListaCheckBox](./accionesOOP/accionListaCheckBox)
- Ejecuta una lista de acciones una tras otra: [accionMacro](./accionesOOP/accionMacro)

### Acciones de ElGarrobo
- Abri interface web: [accionAbrirGUI](./accionesOOP/accionAbrirGUI)
- Recarga acciones dentro del folder: [accionRecargarFolder](./accionesOOP/accionRecargarFolder)
- Entra y carga acciones de un folder: [accionEntrarFolder](./accionesOOP/accionEntrarFolder)
- Entra en un folder en los dispositivos: [accionFolder](./accionesOOP/accionFolder)
- Sube un folder en los dispositivos: [accionRegresarFolder](./accionesOOP/accionRegresarFolder)
- Cierra el programa: [accionSalir](./accionesOOP/accionSalir)
- Reinicia el proceso: [accionReiniciarApp](./accionesOOP/accionReiniciarApp)
- No hace nada (botón solo para mostrar texto): [accionNada](./accionesOOP/accionNada)

### Acciones en StreamDeck
- Anterior pagina de StreamDeck: [accionAnteriorPagina](./accionesOOP/accionAnteriorPagina)
- Siguiente página de StreamDeck: [accionSiguientePagina](./accionesOOP/accionSiguientePagina)
- Actualiza la pagina de StreamDeck: [accionActualizarPagina](./accionesOOP/accionActualizarPagina)

"""

from .accion import accion
from .accionAbrirGUI import accionAbrirGUI
from .accionArchivo import accionEscribirArchivo, accionLeerValor
from .accionBuscarVentana import accionBuscarVentana
from .accionCambiarPagina import (
    accionActualizarPagina,
    accionAnteriorPagina,
    accionSiguientePagina,
)
from .accionCerrarVentana import accionCerrarVentana
from .accionControl import accionControl
from .accionCopiarPapelera import accionCopiarPapelera, accionPegarTexto
from .accionDelay import accionDelay
from .accionEmularRaton import accionEmularRaton
from .accionEntrarFolder import accionEntrarFolder
from .accionEscribirTexto import accionEscribirTexto
from .accionFolder import accionFolder
from .accionListaCheckBox import accionListaCheckBox
from .accionMacro import accionMacro
from .accionMQTT import accionMQTT
from .accionNavegador import accionNavegador
from .accionNotificacion import accionNotificacion
from .accionOS import accionOS
from .accionPresionar import accionPresionar
from .accionPulse import accionMute, accionSalvarPulse, accionVolumen
from .accionRecargarFolder import accionRecargarFolder
from .accionRegresarFolder import accionRegresarFolder
from .accionNada import accionNada
from .accionReiniciarApp import accionReiniciarApp
from .accionSalir import accionSalir
from .accionSonidos import accionPararReproducciones, accionReproducir
from .accionTeclas import accionTeclas
from .accionTelegram import accionTelegram


def cargarClasesAcciones() -> dict[str, type["accion"]]:
    """
    Carga las acciones en una dic con nombre de accion y función asociada.

    Returns:
        (dict): Diccionario con las acciones cargadas
    """

    return {
        "abrir_gui": accionAbrirGUI,
        "mostrar_ventana": accionBuscarVentana,
        "anterior_pagina": accionAnteriorPagina,
        "siguiente_pagina": accionSiguientePagina,
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
        "reiniciar_app": accionReiniciarApp,
        "nada": accionNada,
        "salir": accionSalir,
        "teclas": accionTeclas,
        "raton": accionEmularRaton,
        "telegram": accionTelegram,
        "cerrar_ventana": accionCerrarVentana,
        "copiar": accionCopiarPapelera,
        "pegar": accionPegarTexto,
        "reproduccion": accionReproducir,
        "detener_reproduccion": accionPararReproducciones,
        "presionar": accionPresionar,
        "macro": accionMacro,
        "escribir_archivo": accionEscribirArchivo,
        "leer_valor": accionLeerValor,
        "lista_checkbox": accionListaCheckBox,
        "volumen": accionVolumen,
        "salvar_audio": accionSalvarPulse,
        "mute": accionMute,
    }
