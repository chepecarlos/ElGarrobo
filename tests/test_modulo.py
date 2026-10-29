import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elGarrobo.modulos.fdmMonster.moduloFdmMonster import moduloFdmMonster
from elGarrobo.modulos.modulo import accionesEvento, leerMonitoreo, modulo, propiedadesMonitoreo, reemplazarDatos


def test_leer_monitoreo_usa_defectos_de_las_propiedades():
    defectos = tuple(propiedad.defecto for propiedad in propiedadesMonitoreo())
    assert leerMonitoreo({}) == defectos
    assert leerMonitoreo({"intervalo_segundos": "malo", "limite_errores_log": None}) == defectos


def test_leer_monitoreo_aplica_minimos():
    assert leerMonitoreo({"intervalo_segundos": 1, "limite_errores_log": 0}) == (5, 120, 1)
    assert leerMonitoreo({"intervalo_segundos": 200, "intervalo_error_segundos": 60}) == (200, 200, 3)
    assert leerMonitoreo({"intervalo_segundos": "45"}) == (45, 120, 3), "el texto numérico del archivo se acepta"


def test_reemplazar_datos_solo_los_del_evento():
    opciones = {"texto": "{impresora} terminó", "comando": "awk '{print $1}'", "pasos": [{"opciones": {"t": "{archivo}"}}], "n": 3}
    resultado = reemplazarDatos(opciones, {"impresora": "Ender", "archivo": "a.gcode"})
    assert resultado == {"texto": "Ender terminó", "comando": "awk '{print $1}'", "pasos": [{"opciones": {"t": "a.gcode"}}], "n": 3}
    assert opciones["texto"] == "{impresora} terminó", "no cambia la entrada original de eventos.md"


def test_acciones_evento_filtra_por_evento_activo_y_filtro():
    entradas = [
        {"evento": "x/fin", "accion": "a", "opciones": {"texto": "{impresora}"}},
        {"evento": "x/fin", "accion": "b", "filtro": {"impresora": "Otra"}},
        {"evento": "x/fin", "accion": "c", "activo": False},
        {"evento": "x/inicio", "accion": "d"},
        {"evento": "x/fin", "accion": "e", "filtro": {"progreso": 100}},
    ]
    acciones = accionesEvento(entradas, "x/fin", {"impresora": "Ender", "progreso": "100"})
    assert [a["accion"] for a in acciones] == ["a", "e"], "el filtro compara como texto: 100 del .md = '100' del módulo"
    assert acciones[0]["opciones"]["texto"] == "Ender"


def test_disparar_evento_ejecuta_cada_accion(monkeypatch):
    from elGarrobo import elGarrobo as moduloElGarrobo

    monkeypatch.setattr(moduloElGarrobo, "leerData", lambda _: [{"evento": "x/fin", "accion": "a"}, {"evento": "x/fin", "accion": "b"}])
    app = moduloElGarrobo.elGarrobo.__new__(moduloElGarrobo.elGarrobo)
    app.ejecutarAcción = MagicMock()
    app.dispararEvento("x/fin", {})
    for hilo in [h for h in moduloElGarrobo.threading.enumerate() if h.name == "evento-x/fin"]:
        hilo.join(1)
    assert sorted(llamada.args[0]["accion"] for llamada in app.ejecutarAcción.call_args_list) == ["a", "b"]


class TestEventosFdmMonster:
    API = "http://fdm/api/v2"

    @pytest.fixture
    def fdm(self, monkeypatch):
        """Módulo con FDM Monster simulado: `fdm.pagina` es la primera página y `fdm.sueltos` los trabajos por id"""
        fdm = moduloFdmMonster({"espera_repetidos_segundos": 60})
        fdm.pagina, fdm.sueltos, fdm.avisados = [], {}, []

        def obtener(sesion, url):
            if "search-paged" in url:
                return {"items": fdm.pagina}
            return fdm.sueltos[int(url.rsplit("/", 1)[1])]

        monkeypatch.setattr(fdm, "_obtener_json", obtener)
        monkeypatch.setattr(fdm, "_publicar", MagicMock())
        monkeypatch.setattr(modulo, "funcionEvento", lambda nombre, datos: fdm.avisados.append((nombre, datos)))
        return fdm

    @staticmethod
    def trabajo(id: int, status: str, segundos: int | None = 600, motivo=None, impresora="Ender") -> dict:
        fin = None if segundos is None else f"2026-10-28T10:{segundos // 60:02d}:{segundos % 60:02d}Z"
        return {"id": id, "printerName": impresora, "fileName": "a.gcode", "status": status, "statusReason": motivo, "startedAt": "2026-10-28T10:00:00Z", "endedAt": fin}

    def consultar(self, fdm, *trabajos) -> list[str]:
        fdm.pagina = list(trabajos)
        fdm.avisados.clear()
        fdm._revisar_trabajos(None, self.API)
        return [nombre.removeprefix("fdm_monster/") for nombre, _ in fdm.avisados]

    def test_primera_consulta_no_avisa(self, fdm):
        assert self.consultar(fdm, self.trabajo(5, "PRINTING", None), self.trabajo(4, "COMPLETED")) == []

    def test_inicio_y_fin_aunque_salga_de_la_pagina(self, fdm):
        self.consultar(fdm, self.trabajo(4, "COMPLETED"))
        assert self.consultar(fdm, self.trabajo(5, "PRINTING", None), self.trabajo(4, "COMPLETED")) == ["impresion_iniciada"]
        # Terminó y los fantasma lo empujaron fuera de la primera página: se consulta solo
        fdm.sueltos[5] = self.trabajo(5, "COMPLETED", 1500)
        fantasmas = [self.trabajo(i, "FAILED", 0, "Cancelled", "MK4s") for i in range(30, 10, -1)]
        assert self.consultar(fdm, *fantasmas) == ["impresion_terminada"], "los fantasma de 0s no avisan"
        assert fdm.avisados[0][1] == {"impresora": "Ender", "archivo": "a.gcode", "tiempo_transcurrido": "1500", "tiempo_transcurrido_humano": "25m"}

    def test_cancelada_error_y_motivo(self, fdm):
        self.consultar(fdm, self.trabajo(1, "COMPLETED"))
        error = 'Print submission failed: {"error":"timeout of 30000ms exceeded","stack":"AxiosError..."}'
        eventos = self.consultar(fdm, self.trabajo(3, "FAILED", 600, error), self.trabajo(2, "FAILED", 600, "Cancelled", "Prusa"))
        assert eventos == ["impresion_cancelada", "impresion_error"]
        assert fdm.avisados[1][1]["motivo"] == "Print submission failed: timeout of 30000ms exceeded"

    def test_trabajo_viejo_que_entra_a_la_pagina_no_es_nuevo(self, fdm):
        self.consultar(fdm, self.trabajo(9, "PRINTING", None), self.trabajo(8, "COMPLETED"))
        fdm.sueltos[9] = self.trabajo(9, "PRINTING", None)
        assert self.consultar(fdm, self.trabajo(9, "PRINTING", None), self.trabajo(8, "COMPLETED"), self.trabajo(7, "COMPLETED")) == []

    def test_no_repite_el_mismo_evento_seguido(self, fdm):
        self.consultar(fdm, self.trabajo(1, "COMPLETED"))
        assert self.consultar(fdm, self.trabajo(2, "COMPLETED")) == ["impresion_terminada"]
        assert self.consultar(fdm, self.trabajo(3, "COMPLETED")) == [], "misma impresora antes de 60s"
        assert self.consultar(fdm, self.trabajo(4, "COMPLETED", impresora="Prusa")) == ["impresion_terminada"]

    def test_pausada_avisa_una_vez(self, fdm, monkeypatch):
        socket = {"current": {"payload": {"state": {"text": "Printing"}}}}
        respuestas = {"printer/": [{"id": 1, "name": "Ender", "enabled": True}], "print-queue/1": {"count": 0}, "printer/1/socket": socket}
        monkeypatch.setattr(fdm, "_obtener_json", lambda sesion, url: respuestas[url.removeprefix(self.API + "/")])
        for texto in ("Printing", "Pausing", "Paused", "Printing", "Paused"):
            socket["current"]["payload"]["state"]["text"] = texto
            fdm._consultar_impresoras(None, self.API)
        assert [d["estado"] for _, d in fdm.avisados] == ["Pausing"], "la segunda pausa cae en la espera de repetidos"
