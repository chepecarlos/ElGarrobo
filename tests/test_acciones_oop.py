import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elGarrobo.accionesOOP import accion, accionDelay, accionSecuencia, cargarClasesAcciones
from elGarrobo.accionesOOP.accion import folderEjecución
from elGarrobo.modulos import cargarModulos
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.accionesOOP.herramientas.valoresAccion import valoresAcciones


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
            # Ruta completa del sistema que existe: se usa tal cual, no se pega dentro del perfil
            sonido = tmp_path / "sonidos" / "chan.wav"
            sonido.parent.mkdir()
            sonido.touch()
            assert nueva.calcularRuta(str(sonido)) == str(sonido.resolve())
            # Sin / o con ./: desde el folder del dispositivo que la ejecuta
            enFolder = str((tmp_path / "default" / "ide" / "x.wav").resolve())
            assert nueva.calcularRuta("./x.wav", folder="/ide") == enFolder
            assert nueva.calcularRuta("x.wav", folder="ide") == enFolder
            assert nueva.calcularRuta("/x.wav", folder="/ide") == str((tmp_path / "default" / "x.wav").resolve())
            token = folderEjecución.set("/ide")
            try:
                assert nueva.calcularRuta("./x.wav") == enFolder, "sin folder usa el del dispositivo que ejecuta"
            finally:
                folderEjecución.reset(token)

    def test_str(self):
        assert "Prueba" in str(crearAccion())


def todasLasAcciones() -> dict:
    """Acciones globales más las que agregan los módulos"""
    acciones = cargarClasesAcciones()
    for claseModulo in cargarModulos():
        for claseAccion in claseModulo.acciones:
            assert claseAccion.comando not in acciones, f"{claseAccion.comando} repetido"
            acciones[claseAccion.comando] = claseAccion
    return acciones


class TestCargarClasesAcciones:
    def test_comando_coincide_con_clave_y_se_instancia(self):
        for comando, clase in todasLasAcciones().items():
            instancia = clase()
            assert instancia.comando == comando, clase.__name__
            assert instancia.nombre and instancia.descripcion, clase.__name__

    def test_acciones_base_tienen_categoria(self):
        """Sin categoria quedan en "Otros" del panel de acciones; las de módulos usan el nombre del módulo"""
        sinCategoria = [comando for comando, clase in cargarClasesAcciones().items() if clase.categoria == "Otros"]
        assert sinCategoria == [], f"Falta categoria en: {sinCategoria}"

    def test_propiedades_con_tipos_validos_para_isinstance(self):
        """Un tipo como typing.Any hace que mismoTipo rechace siempre el valor"""
        for comando, clase in todasLasAcciones().items():
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


class TestAccionSecuencia:
    def test_opciones_en_lista_van_a_acciones(self):
        pasos = [{"accion": "delay", "opciones": {"tiempo": 1}}]
        secuencia = accionSecuencia()
        secuencia.configurar(pasos)
        recibido = MagicMock()
        with patch.object(accionSecuencia, "funcionExterna", recibido):
            assert secuencia.ejecutar() is True
        assert recibido.call_args.args[0][0].valor == pasos



@pytest.mark.parametrize("acepta, pasos", [(True, ["confirmar", "cancelar_octoprint", "nada"]), (False, ["confirmar"])])
def test_secuencia_se_detiene_si_no_se_confirma(acepta, pasos):
    from elGarrobo import elGarrobo as moduloElGarrobo
    from elGarrobo.accionesOOP.herramientas.valoresAccion import valoresAcciones

    app = moduloElGarrobo.elGarrobo.__new__(moduloElGarrobo.elGarrobo)
    app.ejecutarAcción = MagicMock(side_effect=lambda comando: acepta if comando["accion"] == "confirmar" else True)
    secuencia = [{"accion": "confirmar"}, {"accion": "cancelar_octoprint"}, {"accion": "nada"}]
    app.ejecutarSecuencia([valoresAcciones("acciones", secuencia)])
    assert [llamada.args[0]["accion"] for llamada in app.ejecutarAcción.call_args_list] == pasos


def test_secuencia_pasa_datos_por_el_cajon():
    from elGarrobo import elGarrobo as moduloElGarrobo
    from elGarrobo.accionesOOP.herramientas.valoresAccion import valoresAcciones

    app = moduloElGarrobo.elGarrobo.__new__(moduloElGarrobo.elGarrobo)
    app.ejecutarAcción = MagicMock(side_effect=lambda comando: "hola" if comando["accion"] == "leer" else True)
    secuencia = [
        {"accion": "leer", "secuencia_opciones": {"respuesta": "texto"}},
        {"accion": "escribir", "secuencia_opciones": {"solicita": "texto"}},
        {"accion": "escribir", "secuencia_opciones": {"solicita": "texto", "solicita_cambiar": "mensaje"}},
    ]
    app.ejecutarSecuencia([valoresAcciones("acciones", secuencia)])
    opciones = [llamada.args[0].get("opciones") for llamada in app.ejecutarAcción.call_args_list]
    assert opciones == [None, {"texto": "hola"}, {"mensaje": "hola"}]


def test_confirmar_sin_entorno_grafico_es_no(monkeypatch):
    from elGarrobo.accionesOOP.accionConfirmar import accionConfirmar

    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    confirmar = accionConfirmar()
    confirmar.configurar({"mensaje": "¿Cancelar?"})
    assert confirmar.ejecutar() is False, "sin ventana no se hace la acción a ciegas"


def test_tecla_ejecuta_en_hilo_salvo_las_de_estado_central():
    import threading

    from elGarrobo import elGarrobo as moduloElGarrobo

    app = moduloElGarrobo.elGarrobo.__new__(moduloElGarrobo.elGarrobo)
    app.listaClasesAcciones = cargarClasesAcciones()
    hilos = {}
    listo = threading.Event()

    def ejecutar(accionActual, estado=True, fuerza=1, folder=None):
        hilos[(accionActual["accion"], estado)] = threading.current_thread()
        if accionActual["accion"] == "secuencia":
            listo.set()

    app.ejecutarAcción = ejecutar
    app.ejecutarTecla({"accion": "secuencia"}, True, 1, "/")
    app.ejecutarTecla({"accion": "entrar_folder"}, True, 1, "/")
    app.ejecutarTecla({"accion": "secuencia"}, False, 1, "/")
    assert listo.wait(2)
    assert hilos[("secuencia", True)] is not threading.current_thread(), "la secuencia no frena las demás teclas"
    assert hilos[("entrar_folder", True)] is threading.current_thread(), "folders y páginas siguen en orden"
    assert hilos[("secuencia", False)] is threading.current_thread(), "soltar no lanza hilos"


def test_confirmar_busca_el_monitor_del_mouse():
    from elGarrobo.accionesOOP.accionConfirmar import monitorEn

    xrandr = "Monitors: 2\n 0: +*DP-1 1920/598x1080/336+0+480  DP-1\n 1: +HDMI-0 800/476x480/268+583+0  HDMI-0\n"
    assert monitorEn(xrandr, 845, 1258) == (1920, 1080, 0, 480)
    assert monitorEn(xrandr, 700, 100) == (800, 480, 583, 0)
    assert monitorEn(xrandr, 100, 100) is None, "fuera de todos: se usa el escritorio entero"
