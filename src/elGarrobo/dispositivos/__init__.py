"""
## Dispositivo base
- Clase que se herencia todas las funciones: [dispositivoBase](./dispositivos/dispositivoBase)

# Lista de Acciones
- Teclado USB: [MiTecladoMacro](./dispositivos/miteclado/mi_teclado_macro)
- Pedal StreamDeck [MiPedal](./dispositivos/mipedal/mi_pedal)
- StreamDeck Combinado [MiDeckCombinado](./dispositivos/mideck/mi_deck_combinado)

"""

from .mideck.mi_deck_combinado import MiDeckCombinado
from .mipedal.mi_pedal import MiPedal
from .miteclado.mi_teclado_macro import MiTecladoMacro


def cargarDispositivos() -> list:

    listaDispositivos: list = [MiTecladoMacro, MiPedal, MiDeckCombinado]

    return listaDispositivos
