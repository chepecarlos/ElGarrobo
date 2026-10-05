from types import SimpleNamespace

from elGarrobo.accionesOOP.herramientas.valoresAccion import valoresAcciones
from elGarrobo.dispositivos.mipedal.mi_pedal import MiPedal
from elGarrobo.elGarrobo import elGarrobo


def crearPedal(teclas: list) -> MiPedal:
    pedal = MiPedal({"nombre": "pedal"})
    pedal._listaAcciones = pedal.convertirAcciones([{"nombre": f"A{tecla}", "key": tecla, "accion": "x"} for tecla in teclas])
    return pedal


def test_paginas_hasta_la_ultima_tecla_con_accion():
    pedal = crearPedal([1, 5])

    pedal.siguientePagina()
    assert pedal.desfaceTeclas == 3
    pedal.siguientePagina()
    assert pedal.desfaceTeclas == 3, "no hay acciones después de la tecla 6"

    pedal.anteriorPagina()
    pedal.anteriorPagina()
    assert pedal.desfaceTeclas == 0


def test_pedal_ejecuta_la_tecla_de_su_pagina():
    pedal = crearPedal([2, "5"])
    ejecutadas = []
    pedal.ejecutarAcción = lambda acción, *args: ejecutadas.append(acción.get("key"))

    pedal.actualizarBoton(None, 1, True)
    pedal.desfaceTeclas = 3
    pedal.actualizarBoton(None, 1, True)

    assert ejecutadas == [2, 5]


def test_pagina_global_no_mueve_el_pedal():
    deck = SimpleNamespace(nombre="Deck", siguientePagina=lambda: None)
    pedal = crearPedal([1])
    garrobo = SimpleNamespace(listaDispositivos=[deck, pedal])

    assert elGarrobo.dispositivosPagina(garrobo, []) == [deck]
    assert elGarrobo.dispositivosPagina(garrobo, [valoresAcciones("dispositivo", "PEDAL")]) == [pedal]
