from typer.testing import CliRunner

from elGarrobo import main, servicio


def test_servicio_instalar_y_desinstalar(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    llamadas = []
    monkeypatch.setattr(servicio.subprocess, "run", lambda comando, **_: llamadas.append(comando))
    runner = CliRunner()

    assert runner.invoke(main.app, ["servicio", "instalar"]).exit_code == 0
    unidad = tmp_path / ".config/systemd/user/elgarrobo.service"
    menu = tmp_path / ".local/share/applications/elgarrobo.desktop"
    inicio = tmp_path / ".config/autostart/elgarrobo.desktop"
    assert "Restart=on-failure" in unidad.read_text()
    assert "bandeja.py" in menu.read_text()
    assert inicio.read_text() == menu.read_text()
    assert ["systemctl", "--user", "daemon-reload"] in llamadas

    assert runner.invoke(main.app, ["servicio", "desinstalar"]).exit_code == 0
    assert not unidad.exists() and not menu.exists() and not inicio.exists()
    assert ["systemctl", "--user", "stop", "elgarrobo"] in llamadas
