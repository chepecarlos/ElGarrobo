import importlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


class DeckFalso:
    def __init__(self):
        self.brillos = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_brightness(self, valor):
        self.brillos.append(valor)


def base():
    """Clase dispositivo que usa MiStreamDeck: ahí vive la última actividad compartida"""
    return importlib.import_module("src.elGarrobo.dispositivos.mideck.mi_streamdeck").dispositivo


def inactivo(segundos):
    base().ultimaActividad = time.monotonic() - segundos


def crear_deck():
    Clase = importlib.import_module("src.elGarrobo.dispositivos.mideck.mi_streamdeck").MiStreamDeck
    deck = Clase.__new__(Clase)
    deck.nombre = "prueba"
    deck.deck = DeckFalso()
    deck.brillo, deck.brilloReposo, deck.minutosReposo = 70, 0, 1
    deck.enReposo = False
    deck._teclaDespertar = None
    inactivo(0)
    deck.ejecutadas = []
    return deck


def simular_padre(monkeypatch, deck):
    monkeypatch.setattr(
        base(), "buscarAccion", lambda self, tecla, estado, fuerza: self.ejecutadas.append((tecla, estado))
    )


def test_brillo_reposo_cero_la_tecla_solo_despierta(monkeypatch):
    deck = crear_deck()
    simular_padre(monkeypatch, deck)

    deck.revisarReposo()
    assert not deck.enReposo and deck.deck.brillos == []

    inactivo(61)
    deck.revisarReposo()
    assert deck.enReposo and deck.deck.brillos == [0]

    # La tecla que despierta no ejecuta nada, ni al presionar ni al soltar
    deck.buscarAccion(3, deck.estadoTecla.PRESIONADA)
    deck.revisarReposo()
    deck.buscarAccion(3, deck.estadoTecla.LIBERADA)
    assert not deck.enReposo and deck.deck.brillos == [0, 70]
    assert deck.ejecutadas == []

    deck.buscarAccion(3, deck.estadoTecla.PRESIONADA)
    assert deck.ejecutadas == [(3, deck.estadoTecla.PRESIONADA)]


def test_minutos_cero_desactiva_reposo():
    deck = crear_deck()
    deck.minutosReposo = 0
    inactivo(10_000)
    deck.revisarReposo()
    assert not deck.enReposo


def test_brillo_reposo_bajo_ejecuta_la_tecla(monkeypatch):
    deck = crear_deck()
    simular_padre(monkeypatch, deck)
    deck.brilloReposo = 10
    inactivo(61)
    deck.revisarReposo()
    assert deck.enReposo

    deck.buscarAccion(3, deck.estadoTecla.PRESIONADA)
    assert deck.ejecutadas == [(3, deck.estadoTecla.PRESIONADA)]
    deck.revisarReposo()
    assert not deck.enReposo and deck.deck.brillos == [10, 70]


def test_nota_reposo_en_gui():
    Combinado = importlib.import_module("src.elGarrobo.dispositivos.mideck.mi_deck_combinado").MiDeckCombinado
    assert "desactivado" in Combinado.notaAparato({})
    assert "solo despierta" in Combinado.notaAparato({"minutos_reposo": 10})
    assert "funcionan normal" in Combinado.notaAparato({"minutos_reposo": 10, "brillo_reposo": 15})


def test_guardar_desde_gui_aplica_sin_reiniciar():
    Combinado = importlib.import_module("src.elGarrobo.dispositivos.mideck.mi_deck_combinado").MiDeckCombinado
    combinado = Combinado.__new__(Combinado)
    deck = crear_deck()
    deck.conectado = True
    combinado.listaDeck = [deck]

    assert combinado.aplicarAparato({"brillo": 40, "minutos_reposo": 5, "brillo_reposo": 10})
    assert (deck.brillo, deck.minutosReposo, deck.brilloReposo) == (40, 5, 10)
    assert deck.deck.brillos == [40]

    # En reposo no enciende la pantalla, el brillo nuevo se pone al despertar
    deck.enReposo = True
    combinado.aplicarAparato({"brillo": 60})
    assert deck.brillo == 60 and deck.deck.brillos == [40]


def test_tecla_de_otro_dispositivo_despierta():
    deck = crear_deck()
    inactivo(61)
    deck.revisarReposo()
    assert deck.enReposo

    teclado = base().__new__(base())
    teclado.nombre = "teclado"
    teclado.listaAcciones = []
    teclado.buscarAccion("KEY_A")
    deck.revisarReposo()
    assert not deck.enReposo and deck.deck.brillos == [0, 70]
