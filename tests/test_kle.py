import sys

from elGarrobo.dispositivos.miteclado import mi_teclado_macro
from elGarrobo.dispositivos.miteclado.kle import convertirKLE

# Copiado de "Download JSON" en keyboard-layout-editor.com (primeras filas del preset ANSI 104 + extras)
kleAnsi = [
    {"name": "Prueba"},
    ["Esc", {"x": 1}, "F1", "F2"],
    [{"y": 0.5}, "~\n`", "!\n1", {"w": 2}, "Backspace"],
    [{"w": 1.5}, "Tab", "Q", "{\n["],
    [{"w": 2.25}, "Shift", "Z", {"w": 2.75}, "Shift"],
    [{"w": 6.25}, "", "&larr;", "<b>Del</b>", "KEY_F13\nG1", "???"],
]


def test_convierte_posiciones_y_keycodes():
    teclas = {t["key"]: t for t in convertirKLE(kleAnsi)}

    assert teclas["KEY_ESC"] == {"key": "KEY_ESC", "x": 0, "y": 0}
    assert teclas["KEY_F1"]["x"] == 2, "x suma el espacio antes de la tecla"
    assert teclas["KEY_GRAVE"] == {"key": "KEY_GRAVE", "x": 0, "y": 1.5, "etiqueta": "`"}
    assert teclas["KEY_BACKSPACE"]["w"] == 2
    assert teclas["KEY_LEFTSHIFT"]["w"] == 2.25 and teclas["KEY_RIGHTSHIFT"]["x"] == 3.25, "segundo Shift es el derecho"
    assert teclas["KEY_SPACE"]["w"] == 6.25 and teclas["KEY_SPACE"]["y"] == 4.5
    assert "KEY_LEFT" in teclas and "KEY_DELETE" in teclas, "entidades y etiquetas HTML se limpian"
    assert teclas["KEY_F13"]["etiqueta"] == "G1", "KEY_ en la leyenda fija el keycode"
    assert len(teclas) == 16, "la tecla sin keycode se omite"


def test_carpeta_del_usuario(tmp_path, monkeypatch):
    import json

    monkeypatch.setattr(sys.modules[mi_teclado_macro.__name__], "ObtenerFolderConfig", lambda: tmp_path)
    (tmp_path / "distribuciones").mkdir()
    (tmp_path / "distribuciones" / "mi_kle.json").write_text(json.dumps(kleAnsi))
    (tmp_path / "distribuciones" / "numpad_17.json").write_text('[{"key": "KEY_A", "x": 0, "y": 0}]')

    assert "mi_kle" in mi_teclado_macro.distribucionesDisponibles()
    assert mi_teclado_macro.cargarDistribucion("mi_kle")[0]["key"] == "KEY_ESC"
    assert mi_teclado_macro.cargarDistribucion("numpad_17") == [{"key": "KEY_A", "x": 0, "y": 0}], "la del usuario reemplaza a la incluida"
