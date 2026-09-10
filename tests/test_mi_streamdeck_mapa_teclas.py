import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def cargar_clase():
    modulo = importlib.import_module("src.elGarrobo.dispositivos.mideck.mi_streamdeck")
    return modulo.MiStreamDeck


class TestMapaTeclas:
    def _crear_deck(self, filas, columnas, rotar):
        Clase = cargar_clase()
        deck = Clase.__new__(Clase)
        deck.layout = (filas, columnas)
        deck.rotar = rotar
        deck._mapaTeclasCache = None
        return deck

    def test_sin_rotar_mantiene_orden_nativo(self):
        deck = self._crear_deck(3, 5, 0)
        logicoANativo, nativoALogico = deck._mapaTeclas()
        assert logicoANativo == list(range(15))
        assert nativoALogico == {i: i for i in range(15)}

    def test_rotar_menos_90_numera_en_orden_de_lectura(self):
        # Layout nativo 3x5 (Stream Deck Original), montado con rotar=-90.
        # Debe leerse en orden de lectura (arriba-abajo, izq-derecha) sobre el
        # layout ya rotado (5x3), en vez del orden column-major que daba el bug.
        deck = self._crear_deck(3, 5, -90)
        logicoANativo, nativoALogico = deck._mapaTeclas()

        assert len(logicoANativo) == 15
        assert sorted(logicoANativo) == list(range(15))

        # La tecla lógica 0 (primera, arriba-izquierda) y la 14 (última,
        # abajo-derecha) deben ser inversos entre lógico y nativo.
        for logico, nativo in enumerate(logicoANativo):
            assert nativoALogico[nativo] == logico

    def test_rotar_180_invierte_el_orden(self):
        deck = self._crear_deck(3, 5, 180)
        logicoANativo, _ = deck._mapaTeclas()
        assert logicoANativo == list(reversed(range(15)))
