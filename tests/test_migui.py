"""Tests de la interfaz web (miGui) con el usuario simulado de nicegui, sin navegador"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from nicegui import ui
from nicegui.testing import User
from nicegui.testing.user_interaction import UserInteraction

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elGarrobo.accionesOOP import cargarClasesAcciones
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.migui import migui as moduloMiGui
from elGarrobo.dispositivos.migui.migui import miGui


class dispositivoFalso(dispositivo):
    """Dispositivo en memoria: no lee ni escribe los archivos del usuario"""

    def __init__(self, nombre: str, tipo: str, acciones: list[dict]) -> None:
        super().__init__({"nombre": nombre})
        self.tipo = tipo
        self.folderActual = "/"
        self._listaAcciones = acciones
        self.vecesSalvado = 0

    def salvarAcciones(self):
        self.vecesSalvado += 1


def accionesIniciales() -> list[dict]:
    return [
        {"nombre": "Uno", "key": 1, "accion": "escribir", "titulo": "", "opciones": {"texto": "hola"}},
        {"nombre": "Dos", "key": 2, "accion": "delay", "titulo": "", "opciones": {"tiempo": 1}},
    ]


@pytest.fixture
def deck() -> dispositivoFalso:
    return dispositivoFalso("deck", "streamdeck", accionesIniciales())


@pytest.fixture
def gui(user: User, deck: dispositivoFalso) -> miGui:
    # Se crea después de `user` porque el fixture reinicia nicegui y miGui registra sus páginas
    gui = miGui({"nombre": "gui"})
    gui.listaClasesAcciones = cargarClasesAcciones()
    gui.listaDispositivos = [deck]
    return gui


async def llenarFormulario(user: User, nombre: str = "", tecla: str = "", acción: str = "", **opciones) -> None:
    if nombre:
        user.find(marker="editorNombre").clear().type(nombre)
    if tecla:
        user.find(marker="editorTecla").clear().type(tecla)
    if acción:
        user.find(marker="editorAcción").click()
        user.find(acción).click()
    for propiedad, valor in opciones.items():
        user.find(marker=f"opción-{propiedad}").clear().type(valor)


def seleccionarPestaña(user: User, gui: miGui, nombre: str) -> None:
    # ponytail: el simulador no cambia el valor de ui.tabs al hacer click, se asigna directo
    with user:
        gui.pestañas.value = nombre


def clickEnDialogoAbierto(user: User, texto: str) -> None:
    # El simulador también encuentra los botones de diálogos cerrados
    botones = [b for b in user.find(texto).elements if any(isinstance(p, ui.dialog) and p.value for p in b.ancestors())]
    assert len(botones) == 1
    UserInteraction(user, {botones[0]}, texto).click()


def teclas(dispositivo: dispositivo) -> list:
    return [a["key"] for a in dispositivo.listaAcciones]


class TestTeclaRepetida:
    def test_detecta_tecla_repetida(self):
        lista = [{"nombre": "a", "key": 1}, {"nombre": "b", "key": 2}]
        assert miGui.teclaRepetida(lista, 2) is lista[1]

    def test_tecla_libre(self):
        assert miGui.teclaRepetida([{"nombre": "a", "key": 1}], 3) is None

    def test_numero_y_texto_son_la_misma_tecla(self):
        lista = [{"nombre": "a", "key": 5}]
        assert miGui.teclaRepetida(lista, "5") is lista[0]

    def test_editar_no_choca_consigo_misma(self):
        lista = [{"nombre": "a", "key": 1}, {"nombre": "b", "key": 2}]
        assert miGui.teclaRepetida(lista, 1, ignorar=lista[0]) is None

    def test_editar_detecta_otra_accion(self):
        lista = [{"nombre": "a", "key": 1}, {"nombre": "b", "key": 2}]
        assert miGui.teclaRepetida(lista, 2, ignorar=lista[0]) is lista[1]

    def test_ignorar_compara_por_identidad(self):
        # Una acción igual en contenido pero distinta en memoria sigue siendo repetida
        lista = [{"nombre": "a", "key": 1}]
        assert miGui.teclaRepetida(lista, 1, ignorar={"nombre": "a", "key": 1}) is lista[0]


class TestOrdenTecla:
    def test_numeros_antes_que_texto(self):
        lista = [{"key": "b"}, {"key": 10}, {"key": "a"}, {"key": 2}]
        lista.sort(key=miGui.ordenTecla)
        assert [a["key"] for a in lista] == [2, 10, "a", "b"]


class TestOrdenarAcciones:
    lista = [{"nombre": "b", "key": 2, "accion": "os"}, {"nombre": "A", "key": 1, "accion": "escribir"}]

    def test_por_nombre_ignora_mayusculas(self):
        assert [a["nombre"] for a in miGui.ordenarAcciones(self.lista, "nombre")] == ["A", "b"]

    def test_por_accion_inverso(self):
        assert [a["accion"] for a in miGui.ordenarAcciones(self.lista, "accion", True)] == ["os", "escribir"]

    def test_no_modifica_lista_original(self):
        miGui.ordenarAcciones(self.lista, "key")
        assert self.lista[0]["key"] == 2


class TestPaginaAcciones:
    async def test_muestra_acciones_y_cabecera(self, user: User, gui: miGui):
        await user.open("/")
        await user.should_see("Uno")
        await user.should_see("Dos")
        await user.should_see("Escribir texto")
        await user.should_see("streamdeck")
        await user.should_see(marker="editar-deck-1")

    async def test_agregar_accion(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        await llenarFormulario(user, "Tres", "3", "Escribir texto", Texto="adios")
        user.find(marker="botonAgregar").click()

        await user.should_see("Agregando acción Tres")
        nueva = deck.listaAcciones[-1]
        assert nueva.aDict() == {"nombre": "Tres", "key": 3, "accion": "escribir", "titulo": "", "opciones": {"texto": "adios"}}
        assert deck.vecesSalvado == 1
        await user.should_see(marker="editar-deck-3")
        assert gui.editorNombre.value == ""

    async def test_agregar_ordena_por_tecla(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        await llenarFormulario(user, "Cero", "0", "Delay", Tiempo="1")
        user.find(marker="botonAgregar").click()
        assert teclas(deck) == [0, 1, 2]

    async def test_tecla_repetida_no_se_guarda(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        await llenarFormulario(user, "Otra", "1", "Escribir texto", Texto="x")
        user.find(marker="botonAgregar").click()

        await user.should_see("La tecla 1 ya está usada por 'Uno', cámbiela")
        assert teclas(deck) == [1, 2]
        assert deck.vecesSalvado == 0
        assert gui.editorNombre.value == "Otra", "el formulario no se limpia para poder corregir"

    @pytest.mark.parametrize(
        "campos, mensaje",
        [
            ({}, "Ingrese un nombre"),
            ({"nombre": "A"}, "Ingrese una tecla"),
            ({"nombre": "A", "tecla": "9"}, "Seleccione una acción"),
            ({"nombre": "A", "tecla": "x", "acción": "Delay"}, "Error con tecla no numero"),
        ],
    )
    async def test_validaciones(self, user: User, gui: miGui, deck: dispositivoFalso, campos, mensaje):
        await user.open("/")
        await llenarFormulario(user, **campos)
        user.find(marker="botonAgregar").click()
        await user.should_see(mensaje)
        assert deck.vecesSalvado == 0

    async def test_propiedad_obligatoria(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        await llenarFormulario(user, "Tres", "3", "Escribir texto")
        user.find(marker="botonAgregar").click()
        await user.should_see("Error Texto es Obligatorio")
        assert deck.vecesSalvado == 0

    async def test_editar_llena_formulario(self, user: User, gui: miGui):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        assert gui.botonAgregar.icon == "edit"
        assert gui.editorNombre.value == "Uno"
        assert gui.editorTecla.value == 1
        assert gui.editorAcción.value == "Escribir texto"
        assert gui.opcionesEditar["Texto"].value == "hola"

    async def test_cambiar_accion_mantiene_propiedades(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        await llenarFormulario(user, acción="Pegar texto")
        assert gui.opcionesEditar["Texto"].value == "hola"

        user.find(marker="botonAgregar").click()
        await user.should_see("Editar acción Uno")
        assert deck.listaAcciones[0]["accion"] == "pegar"
        assert deck.listaAcciones[0]["opciones"] == {"texto": "hola"}

    async def test_editar_otra_accion_no_arrastra_valores(self, user: User, gui: miGui, deck: dispositivoFalso):
        deck.listaAcciones.append({"nombre": "Tres", "key": 3, "accion": "pegar", "titulo": "", "opciones": {}})
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        user.find(marker="editar-deck-3").click()
        assert gui.opcionesEditar["Texto"].value in ("", None)

    async def test_editar_misma_tecla(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        await llenarFormulario(user, nombre="Uno editado", Texto="chao")
        user.find(marker="botonAgregar").click()

        await user.should_see("Editar acción Uno editado")
        assert len(deck.listaAcciones) == 2
        assert deck.listaAcciones[0]["nombre"] == "Uno editado"
        assert deck.listaAcciones[0]["opciones"] == {"texto": "chao"}
        assert deck.vecesSalvado == 1
        assert gui.botonAgregar.icon == "add"

    async def test_editar_a_tecla_ocupada(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        await llenarFormulario(user, tecla="2")
        user.find(marker="botonAgregar").click()

        await user.should_see("La tecla 2 ya está usada por 'Dos', cámbiela")
        assert teclas(deck) == [1, 2]
        assert deck.vecesSalvado == 0

    async def test_editar_cambiar_tecla_reordena(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        await llenarFormulario(user, tecla="5")
        user.find(marker="botonAgregar").click()
        assert teclas(deck) == [2, 5]

    async def test_limpiar_cancela_edición(self, user: User, gui: miGui):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        user.find(marker="botonLimpiar").click()
        assert gui.botonAgregar.icon == "add"
        assert gui.accionEditar is None
        assert gui.editorNombre.value == ""

    async def test_borrar_accion(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="borrar-deck-2").click()
        assert teclas(deck) == [1]
        assert deck.vecesSalvado == 1
        await user.should_not_see(marker="editar-deck-2")

    async def test_ejecutar_accion(self, user: User, gui: miGui, deck: dispositivoFalso):
        gui.ejecutarAcción = MagicMock()
        await user.open("/")
        user.find(marker="ejecutar-deck-2").click()
        gui.ejecutarAcción.assert_called_once_with(deck.listaAcciones[1])


class TestPestañas:
    async def test_agrega_en_pestaña_seleccionada(self, user: User, gui: miGui, deck: dispositivoFalso):
        teclado = dispositivoFalso("teclado", "teclado", [{"nombre": "Copiar", "key": "a", "accion": "delay"}])
        teclado.nivelOrdenar = -1
        gui.listaDispositivos.append(teclado)
        await user.open("/")
        seleccionarPestaña(user, gui, "teclado")
        await llenarFormulario(user, "Pegar", "b", "Delay", Tiempo="1")
        user.find(marker="botonAgregar").click()

        assert teclas(teclado) == ["a", "b"], "en teclados la tecla queda como texto"
        assert teclas(deck) == [1, 2]

    async def test_misma_tecla_en_otro_dispositivo_permitida(self, user: User, gui: miGui, deck: dispositivoFalso):
        otro = dispositivoFalso("pedal", "pedal", [])
        otro.nivelOrdenar = -1
        gui.listaDispositivos.append(otro)
        await user.open("/")
        seleccionarPestaña(user, gui, "pedal")
        await llenarFormulario(user, "Pie", "1", "Delay", Tiempo="1")
        user.find(marker="botonAgregar").click()
        assert teclas(otro) == [1]


class TestMenu:
    @pytest.mark.parametrize("item, comando", [("Salir", "salir"), ("Reiniciar", "reiniciar_app")])
    async def test_confirmar_accion_sistema(self, user: User, gui: miGui, item, comando):
        gui.ejecutarAccionSistema = MagicMock()
        await user.open("/")
        user.find(marker=f"menu-{item}").click()
        clickEnDialogoAbierto(user, "Confirmar")
        gui.ejecutarAccionSistema.assert_called_once_with(comando)

    async def test_cancelar_no_ejecuta(self, user: User, gui: miGui):
        gui.ejecutarAccionSistema = MagicMock()
        await user.open("/")
        user.find(marker="menu-Salir").click()
        clickEnDialogoAbierto(user, "Cancelar")
        gui.ejecutarAccionSistema.assert_not_called()

    @pytest.mark.parametrize("item, ruta", [("Módulos", "/modulos"), ("Dispositivos", "/dispositivos"), ("Acciones", "/")])
    async def test_navegar(self, user: User, gui: miGui, monkeypatch, item, ruta):
        monkeypatch.setattr(moduloMiGui, "leerData", lambda _: {})
        await user.open("/modulos")
        user.find(marker=f"menu-{item}").click()
        for _ in range(20):  # la navegación corre en segundo plano
            if user.back_history[-1] == ruta:
                break
            await asyncio.sleep(0.05)
        assert user.back_history[-1] == ruta

    async def test_accion_sistema_inexistente(self, user: User, gui: miGui):
        gui.listaClasesAcciones = {}
        await user.open("/")
        with user:
            gui.ejecutarAccionSistema("salir")
        await user.should_see("No se encontró la acción salir")


class TestActivables:
    @pytest.mark.parametrize("ruta, archivo", [("/modulos", "modulos"), ("/dispositivos", "dispositivos")])
    async def test_switch_guarda_estado(self, user: User, gui: miGui, monkeypatch, ruta, archivo):
        salvar = MagicMock()
        monkeypatch.setattr(moduloMiGui, "leerData", lambda _: {})
        monkeypatch.setattr(moduloMiGui, "SalvarValor", salvar)
        await user.open(ruta)
        await user.should_see("Los cambios requieren reiniciar elgarrobo para aplicarse")

        switch = next(iter(user.find(kind=ui.switch).elements))
        with user:
            switch.value = True
        assert salvar.call_args.args[0] == archivo
        assert salvar.call_args.args[2] is True
        await user.should_see("activado - reiniciá elgarrobo para aplicar")

