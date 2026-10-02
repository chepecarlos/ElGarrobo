import importlib

modulo = importlib.import_module("elGarrobo.accionesOOP.accionAbrirGUI")


def test_puerto_primera_gui_activada(monkeypatch):
    monkeypatch.setattr(modulo, "ObtenerArchivo", lambda _: [{"activado": False, "puerto": 1}, {"puerto": 8383}])
    assert modulo.obtenerPuertoGUI() == 8383


def test_puerto_default_sin_config(monkeypatch):
    monkeypatch.setattr(modulo, "ObtenerArchivo", lambda _: None)
    assert modulo.obtenerPuertoGUI() == 8080
