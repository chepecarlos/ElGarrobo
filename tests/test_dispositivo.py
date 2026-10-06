import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elGarrobo.dispositivos.dispositivo import dispositivo

# El paquete exporta la clase con el mismo nombre que el módulo
moduloDispositivo = sys.modules["elGarrobo.dispositivos.dispositivo"]


def test_salvar_acciones_quita_claves_internas(monkeypatch, tmp_path):
    salvar = MagicMock()
    monkeypatch.setattr(moduloDispositivo, "ObtenerFolderConfig", lambda: tmp_path)
    monkeypatch.setattr(moduloDispositivo, "SalvarArchivo", salvar)

    disp = dispositivo({"nombre": "deck", "archivo": "deck"})
    disp.folderActual = "/"
    acción = {"nombre": "Uno", "key": 1, "__estado": True, "__otro": 2}
    disp.listaAcciones = [acción]

    disp.salvarAcciones()

    archivo, guardadas = salvar.call_args.args
    assert archivo == str(tmp_path / "default" / "deck.md")
    assert guardadas == [{"nombre": "Uno", "key": 1}]
    assert acción["__estado"] is True, "no modifica las acciones en memoria"


def test_gui_se_avisa_con_el_folder_ya_cambiado(monkeypatch, tmp_path):
    from elGarrobo.dispositivos.mideck.mi_deck_combinado import MiDeckCombinado

    monkeypatch.setattr(moduloDispositivo, "ObtenerFolderConfig", lambda: tmp_path)
    (tmp_path / "default" / "sub").mkdir(parents=True)
    (tmp_path / "default" / "streamdeck.json").write_text('[{"nombre": "Raiz", "key": 1}]')
    (tmp_path / "default" / "sub" / "streamdeck.json").write_text('[{"nombre": "Sub", "key": 1}]')

    combinado = MiDeckCombinado({"nombre": "combinado", "archivo": "streamdeck", "streamDecks": [{"nombre": "V2"}]})
    combinado.asignarPerfil("default")
    vistos = []
    combinado.funcionActualizarPestaña = lambda d: vistos.append((str(d.listaDeck[0].folderActual), d.listaAcciones[0].nombre))

    combinado.cargarAccionesFolder("/")
    combinado.cargarAccionesFolder("sub")
    combinado.cargarAccionesFolder("/")

    assert vistos == [(".", "Raiz"), ("sub", "Sub"), (".", "Raiz")]
