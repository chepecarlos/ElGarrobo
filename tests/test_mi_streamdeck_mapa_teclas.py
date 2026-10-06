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


class TestGruposBotones:
    def _crear_deck(self, nombre, layout, rotar, base):
        Clase = cargar_clase()
        deck = Clase({"nombre": nombre, "rotar": rotar})
        deck.layout = layout
        deck.baseTeclas = base
        return deck

    def test_rotado_se_ve_al_reves(self):
        normal = self._crear_deck("V2", (3, 5), 0, 1).gruposBotones()[0]
        rotado = self._crear_deck("V1", (3, 5), -90, 16).gruposBotones()[0]

        assert (normal.filas, normal.columnas, normal.primeraTecla) == (3, 5, 1)
        assert (rotado.filas, rotado.columnas, rotado.primeraTecla) == (5, 3, 16)

    def test_combinado_junta_sus_streamdecks_y_sigue_la_pagina(self):
        from elGarrobo.dispositivos.mideck.mi_deck_combinado import MiDeckCombinado

        combinado = MiDeckCombinado({"nombre": "combinado", "streamDecks": [{"nombre": "V2"}, {"nombre": "V1", "rotar": -90}]})
        for deck, base in zip(combinado.listaDeck, (1, 16)):
            deck.layout = (3, 5)
            deck.baseTeclas = base
            deck.desfaceTeclas = 30

        grupos = combinado.gruposBotones()

        assert [(g.nombre, g.filas, g.columnas, g.primeraTecla) for g in grupos] == [("V2", 3, 5, 31), ("V1", 5, 3, 46)]
        assert grupos[1].dibujante is combinado.listaDeck[1]


def test_gui_muestra_el_icono_derecho_en_aparato_rotado(tmp_path):
    from PIL import Image

    from elGarrobo.dispositivos.dataAccion import dataAccion
    from elGarrobo.dispositivos.dibujoBoton import dibujoBoton

    # Mitad izquierda roja: rotado -90 en el aparato, sin rotar en la GUI
    Image.new("RGB", (72, 72), "blue").save(tmp_path / "icono.png")
    icono = Image.open(tmp_path / "icono.png")
    icono.paste((255, 0, 0), (0, 0, 36, 72))
    icono.save(tmp_path / "icono.png")

    dibujo = dibujoBoton(folderPerfil=tmp_path, rotar=-90)
    acción = dataAccion(imagen="icono.png")

    enAparato = dibujo.dibujar(acción, (72, 72))
    enGui = dibujo.dibujar(acción, (72, 72), compensarRotar=-90)

    assert enGui.getpixel((5, 36)) == (255, 0, 0), "la GUI lo muestra como el archivo"
    assert enAparato.getpixel((5, 36)) != (255, 0, 0), "el aparato lo gira para compensar su montaje"


def test_combinado_avisa_a_la_gui_al_cambiar_de_pagina():
    from elGarrobo.dispositivos.dataAccion import dataAccion
    from elGarrobo.dispositivos.mideck.mi_deck_combinado import MiDeckCombinado

    combinado = MiDeckCombinado({"nombre": "combinado", "streamDecks": [{"nombre": "V2"}]})
    combinado.cantidadBotones = 15
    combinado._listaAcciones = [dataAccion(key=40)]
    avisos = []
    combinado.funcionActualizarPestaña = avisos.append

    combinado.siguientePagina()
    combinado.anteriorPagina()

    assert avisos == [combinado, combinado]


def test_cambio_de_fondo_del_folder_redibuja_los_botones():
    from elGarrobo.dispositivos.dataAccion import dataAccion

    deck = cargar_clase()({"nombre": "V2"})
    acción = dataAccion(key=1, titulo="A")
    deck._listaAcciones = [acción, dataAccion(key="propiedad_folder", imagenOpciones={"fondo": "#000000"})]
    antes = deck.opcionesDibujo(acción)

    deck.propiedadFolder.fondo = "#ff0000"

    assert deck.opcionesDibujo(acción) != antes
