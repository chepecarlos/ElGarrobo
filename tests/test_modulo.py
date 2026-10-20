import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elGarrobo.modulos.modulo import leerMonitoreo, propiedadesMonitoreo


def test_leer_monitoreo_usa_defectos_de_las_propiedades():
    defectos = tuple(propiedad.defecto for propiedad in propiedadesMonitoreo())
    assert leerMonitoreo({}) == defectos
    assert leerMonitoreo({"intervalo_segundos": "malo", "limite_errores_log": None}) == defectos


def test_leer_monitoreo_aplica_minimos():
    assert leerMonitoreo({"intervalo_segundos": 1, "limite_errores_log": 0}) == (5, 120, 1)
    assert leerMonitoreo({"intervalo_segundos": 200, "intervalo_error_segundos": 60}) == (200, 200, 3)
    assert leerMonitoreo({"intervalo_segundos": "45"}) == (45, 120, 3), "el texto numérico del archivo se acepta"
