import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def cargar_modulo_estado_pc():
    return importlib.import_module("src.elGarrobo.modulos.estadoPc")


class TestEstadoPc:
    def test_crea_archivo_configuracion_con_valor_por_defecto(self, tmp_path, monkeypatch):
        estado_pc_module = cargar_modulo_estado_pc()
        monkeypatch.setattr(estado_pc_module, "ObtenerFolderConfig", lambda: tmp_path)

        modulo = estado_pc_module.estadoPc({})
        archivo_configuracion = tmp_path / "modulos" / "estado_pc.md"

        assert archivo_configuracion.exists()
        with archivo_configuracion.open() as archivo:
            data = list(yaml.safe_load_all(archivo))[0]

        assert data == {"nombre_pc": "pc-default"}
        assert modulo.nombrePC == "pc-default"

    def test_no_sobrescribe_archivo_existente(self, tmp_path, monkeypatch):
        estado_pc_module = cargar_modulo_estado_pc()
        monkeypatch.setattr(estado_pc_module, "ObtenerFolderConfig", lambda: tmp_path)

        archivo_configuracion = tmp_path / "modulos" / "estado_pc.md"
        archivo_configuracion.parent.mkdir(parents=True, exist_ok=True)
        archivo_configuracion.write_text("---\nnombre_pc: pc-oficina\n...\n", encoding="utf-8")

        modulo = estado_pc_module.estadoPc({"nombre_pc": "pc-oficina"})

        with archivo_configuracion.open() as archivo:
            data = list(yaml.safe_load_all(archivo))[0]

        assert data == {"nombre_pc": "pc-oficina"}
        assert modulo.nombrePC == "pc-oficina"

    def test_ejecutar_solo_inicia_hilo_una_vez(self, tmp_path, monkeypatch):
        estado_pc_module = cargar_modulo_estado_pc()
        monkeypatch.setattr(estado_pc_module, "ObtenerFolderConfig", lambda: tmp_path)

        hilos_creados = []

        class HiloFalso:
            def __init__(self, target, daemon):
                self.target = target
                self.daemon = daemon
                self.iniciado = False
                hilos_creados.append(self)

            def start(self):
                self.iniciado = True

        monkeypatch.setattr(estado_pc_module.threading, "Thread", HiloFalso)

        modulo = estado_pc_module.estadoPc({})
        modulo.ejecutar()
        modulo.ejecutar()

        assert len(hilos_creados) == 1
        assert hilos_creados[0].iniciado is True
        assert modulo.activo is True

    def test_monitorear_publica_cpu_y_ram(self, tmp_path, monkeypatch):
        estado_pc_module = cargar_modulo_estado_pc()
        monkeypatch.setattr(estado_pc_module, "ObtenerFolderConfig", lambda: tmp_path)

        class MemoriaFalsa:
            percent = 66.7

        mensajes_publicados = []

        class MqttFalso:
            def configurar(self, data):
                self.data = data

            def ejecutar(self):
                mensajes_publicados.append(self.data)

        def dormir_falso(_segundos):
            modulo.activo = False

        monkeypatch.setattr(estado_pc_module.psutil, "cpu_percent", lambda interval: 42.5)
        monkeypatch.setattr(estado_pc_module.psutil, "virtual_memory", lambda: MemoriaFalsa())
        monkeypatch.setattr(estado_pc_module, "accionMQTT", MqttFalso)
        monkeypatch.setattr(estado_pc_module.time, "sleep", dormir_falso)

        modulo = estado_pc_module.estadoPc({"nombre_pc": "pc-lab"})
        modulo.activo = True
        modulo._monitorear_recursos()

        assert mensajes_publicados == [
            {"topic": "estado_pc/pc-lab/cpu", "mensaje": "42.5"},
            {"topic": "estado_pc/pc-lab/ram", "mensaje": "66.7"},
        ]

    def test_monitorear_registra_error_si_falla_cpu(self, tmp_path, monkeypatch):
        estado_pc_module = cargar_modulo_estado_pc()
        monkeypatch.setattr(estado_pc_module, "ObtenerFolderConfig", lambda: tmp_path)

        monkeypatch.setattr(
            estado_pc_module.psutil,
            "cpu_percent",
            lambda interval: (_ for _ in ()).throw(RuntimeError("fallo cpu")),
        )

        logger_falso = MagicMock()
        monkeypatch.setattr(estado_pc_module, "logger", logger_falso)

        modulo = estado_pc_module.estadoPc({"nombre_pc": "pc-lab"})
        modulo.activo = True
        modulo._monitorear_recursos()

        assert modulo.activo is True
        logger_falso.error.assert_called_once()
