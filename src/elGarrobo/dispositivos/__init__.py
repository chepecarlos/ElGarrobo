"""
## Dispositivo base
- Clase que se herencia todas las funciones: [dispositivoBase](./dispositivos/dispositivoBase)

# Lista de Acciones
- Teclado USB: [MiTecladoMacro](./dispositivos/miteclado/mi_teclado_macro)

"""

from .mipedal.mi_pedal import MiPedal
from .miteclado.mi_teclado_macro import MiTecladoMacro


def cargarDispositivos() -> list:

    listaDispositivos: list = [MiTecladoMacro, MiPedal]

    return listaDispositivos
