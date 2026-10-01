import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elGarrobo.accionesOOP import accion, accionDelay, cargarClasesAcciones
from elGarrobo.accionesOOP.heramientas.propiedadAccion import propiedadAccion
from elGarrobo.accionesOOP.heramientas.valoresAccion import valoresAcciones


def crearAccion(*propiedades: propiedadAccion) -> accion:
    nueva = accion("Prueba", "prueba", "accion de prueba")
    for propiedad in propiedades:
        nueva.agregarPropiedad(propiedad)
    return nueva


class TestPropiedadAccion:
    def test_tipo_unico_se_normaliza_a_lista(self):
        assert propiedadAccion("N", "n", tipo=str).tipo == [str]

    def test_mismo_tipo(self):
        propiedad = propiedadAccion("N", "n", tipo=[int, str])
        assert propiedad.mismoTipo(1)
        assert propiedad.mismoTipo("a")
        assert not propiedad.mismoTipo(1.5)

    def test_sin_tipo_acepta_todo(self):
        assert propiedadAccion("N", "n", tipo=[]).mismoTipo(object())

    def test_mismo_atributo_con_str_y_valor(self):
        propiedad = propiedadAccion("N", "n")
        assert propiedad.mismoAtributo("n")
        assert propiedad.mismoAtributo(valoresAcciones("n", 1))
        assert not propiedad.mismoAtributo("otro")

    def test_igualdad_con_valor_y_propiedad(self):
        propiedad = propiedadAccion("N", "n")
        assert propiedad == valoresAcciones("n", 1)
        assert propiedad == propiedadAccion("Otro", "n")
        assert propiedad != valoresAcciones("x", 1)


class TestAccionBase:
    def test_configurar_guarda_valores_validos(self):
        nueva = crearAccion(propiedadAccion("T", "texto", tipo=str))
        nueva.configurar({"texto": "hola"})
        assert nueva.obtenerValor("texto") == "hola"
        assert not nueva.error

    def test_configurar_ignora_atributo_extra(self):
        nueva = crearAccion(propiedadAccion("T", "texto", tipo=str))
        nueva.configurar({"extra": 1})
        assert nueva.listaValores == []
        assert not nueva.error

    def test_configurar_tipo_incorrecto_marca_error(self):
        nueva = crearAccion(propiedadAccion("T", "texto", tipo=str))
        nueva.configurar({"texto": 5})
        assert nueva.error
        assert not nueva.sePuedeEjecutar()

    def test_configurar_none_limpia_valores(self):
        nueva = crearAccion(propiedadAccion("T", "texto", tipo=str))
        nueva.configurar({"texto": "a"})
        nueva.configurar(None)
        assert nueva.listaValores == []

    def test_falta_propiedad_obligatoria(self):
        nueva = crearAccion(propiedadAccion("T", "texto", tipo=str, obligatorio=True))
        nueva.configurar({})
        assert not nueva.sePuedeEjecutar()
        assert nueva.ejecutar() is False

    def test_obtener_valor_usa_defecto_y_default(self):
        nueva = crearAccion(propiedadAccion("T", "texto", tipo=str, defecto="d"), propiedadAccion("O", "otro"))
        nueva.configurar({})
        assert nueva.obtenerValor("texto") == "d"
        assert nueva.obtenerValor("otro", "x") == "x"

    def test_ejecutar_llama_funcion(self):
        nueva = crearAccion()
        nueva.funcion = MagicMock()
        nueva.configurar({})
        assert nueva.ejecutar() is True
        nueva.funcion.assert_called_once()

    def test_ejecutar_llama_funcion_externa_con_valores(self):
        nueva = crearAccion(propiedadAccion("T", "texto", tipo=str))
        nueva.funcionExterna = MagicMock()
        nueva.configurar({"texto": "a"})
        assert nueva.ejecutar() is True
        nueva.funcionExterna.assert_called_once_with(nueva.listaValores)

    def test_ejecutar_sin_funcion(self):
        nueva = crearAccion()
        nueva.configurar({})
        assert nueva.ejecutar() is False

    def test_configurar_fuerza(self):
        nueva = crearAccion()
        nueva.configurarFuerza(3)
        assert nueva.fuerza == 3

    def test_calcular_ruta(self, tmp_path):
        nueva = crearAccion()
        with patch("elGarrobo.accionesOOP.accion.ObtenerFolderConfig", return_value=str(tmp_path)):
            assert nueva.calcularRuta("a.md") == str((tmp_path / "default" / "a.md").resolve())
            assert nueva.calcularRuta("/b/a.md") == str((tmp_path / "default" / "b" / "a.md").resolve())

    def test_str(self):
        assert "Prueba" in str(crearAccion())


class TestCargarClasesAcciones:
    def test_comando_coincide_con_clave_y_se_instancia(self):
        for comando, clase in cargarClasesAcciones().items():
            instancia = clase()
            assert instancia.comando == comando, clase.__name__
            assert instancia.nombre and instancia.descripcion, clase.__name__

    def test_propiedades_con_tipos_validos_para_isinstance(self):
        """Un tipo como typing.Any hace que mismoTipo rechace siempre el valor"""
        for comando, clase in cargarClasesAcciones().items():
            for propiedad in clase().listaPropiedades:
                for tipo in propiedad.tipo:
                    try:
                        isinstance(None, tipo)
                    except TypeError:
                        pytest.fail(f"{comando}.{propiedad.atributo} usa tipo invalido {tipo}")


class TestAccionDelay:
    @pytest.mark.parametrize("tiempo, segundos", [(2, 2), ("5", 5), ("1:30", 90), ("1:01:01", 3661)])
    def test_convierte_tiempo(self, tiempo, segundos):
        delay = accionDelay()
        delay.configurar({"tiempo": tiempo})
        with patch("elGarrobo.accionesOOP.accionDelay.time.sleep") as dormir:
            assert delay.ejecutar() is True
        dormir.assert_called_once_with(segundos)

    def test_sin_tiempo_no_ejecuta(self):
        delay = accionDelay()
        delay.configurar({})
        assert delay.ejecutar() is False
