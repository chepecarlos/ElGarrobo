"""
## Dispositivo base
- Clase que se herencia todas las funciones: [dispositivo](./dispositivos/dispositivo)

# Lista de Acciones
- Teclado USB: [MiTecladoMacro](./dispositivos/miteclado/mi_teclado_macro)
- Pedal StreamDeck [MiPedal](./dispositivos/mipedal/mi_pedal)
- StreamDeck Combinado [MiDeckCombinado](./dispositivos/mideck/mi_deck_combinado)

"""

from .dispositivo import dispositivo
from .mideck.mi_deck_combinado import MiDeckCombinado
from .migui.migui import miGui
from .mimqtt.mi_mqtt import MiMQTT
from .mipedal.mi_pedal import MiPedal
from .miteclado.mi_teclado_macro import MiTecladoMacro


def cargarDispositivos() -> list:

    listaDispositivos: list = [MiTecladoMacro, MiPedal, MiDeckCombinado, miGui]

    return listaDispositivos
