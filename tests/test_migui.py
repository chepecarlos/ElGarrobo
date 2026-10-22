"""Tests de la interfaz web (miGui) con el usuario simulado de nicegui, sin navegador"""

import asyncio
import base64
import io
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from nicegui import ui
from PIL import Image
from nicegui.testing import User
from nicegui.testing.user_interaction import UserInteraction

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elGarrobo.accionesOOP import cargarClasesAcciones
from elGarrobo.dispositivos.dataAccion import dataAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.mideck.mi_deck_combinado import MiDeckCombinado
from elGarrobo.dispositivos.mipedal.mi_pedal import MiPedal
from elGarrobo.dispositivos.miteclado.mi_teclado_macro import MiTecladoMacro, folderDistribuciones
from elGarrobo.dispositivos.migui import migui as moduloMiGui
from elGarrobo.dispositivos.migui import configuracion, tema, vistas
from elGarrobo.dispositivos.migui import teclas as moduloTeclas
from elGarrobo.dispositivos.migui.migui import miGui


class dispositivoFalso(dispositivo):
    """Dispositivo en memoria: no lee ni escribe los archivos del usuario"""

    def __init__(self, nombre: str, tipo: str, acciones: list[dict]) -> None:
        super().__init__({"nombre": nombre})
        self.tipo = tipo
        self.folderActual = "/"
        self._listaAcciones = self.convertirAcciones(acciones)
        self.vecesSalvado = 0

    def salvarAcciones(self):
        self.vecesSalvado += 1


@pytest.fixture(autouse=True)
def distribucionesUsuario(monkeypatch, tmp_path) -> Path:
    """Las distribuciones propias del usuario en una carpeta temporal, no en su config real"""
    folder = tmp_path / "distribuciones"
    monkeypatch.setattr(sys.modules[MiTecladoMacro.__module__], "folderDistribucionesUsuario", lambda: folder)
    return folder


def imagenVista(url: str) -> Image.Image:
    """Imagen que sirve /vista/{hash} para una tecla de la cuadrícula"""
    contenido, _ = vistas._vistas[url.removeprefix("/vista/")]
    return Image.open(io.BytesIO(contenido))


def test_url_vista_por_contenido():
    roja = Image.new("RGB", (8, 8), "red")
    url = vistas.urlVista(roja)
    assert url == vistas.urlVista(roja.copy()), "misma imagen, misma URL: el navegador la reusa"
    assert url != vistas.urlVista(Image.new("RGB", (8, 8), "blue"))
    respuesta = vistas.servirVista(url.removeprefix("/vista/"))
    assert respuesta.media_type == "image/png" and "immutable" in respuesta.headers["cache-control"]
    assert imagenVista(url).convert("RGB").getpixel((1, 1)) == (255, 0, 0)
    assert vistas.servirVista("no-existe").status_code == 404
    # los gifs llegan como data URI WebP y se sirven con su tipo
    webp = vistas.urlVista("data:image/webp;base64," + base64.b64encode(b"RIFF").decode())
    assert vistas.servirVista(webp.removeprefix("/vista/")).media_type == "image/webp"


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
        user.find(marker="editor-nombre").clear().type(nombre)
    if tecla:
        user.find(marker="editor-key").clear().type(tecla)
    if acción:
        user.find(marker="editorAcción").click()
        user.find(acción).click()
    for propiedad, valor in opciones.items():
        user.find(marker=f"opción-{propiedad}").clear().type(valor)


def seleccionarPestaña(user: User, gui: miGui, nombre: str) -> None:
    # ponytail: el simulador no cambia el valor de ui.tabs al hacer click, se asigna directo
    with user:
        gui.pestañas.tabs.value = nombre


def clickEnDialogoAbierto(user: User, texto: str) -> None:
    # El simulador también encuentra los botones de diálogos cerrados
    botones = [b for b in user.find(kind=ui.button, content=texto).elements if any(isinstance(p, ui.dialog) and p.value for p in b.ancestors())]
    assert len(botones) == 1
    UserInteraction(user, {botones[0]}, texto).click()


async def esperarQue(condición, segundos: float = 1) -> None:
    """Para cambios que nicegui dibuja en el siguiente ciclo (refresh, tareas de fondo) y should_see no revisa"""
    for _ in range(int(segundos / 0.05)):
        if condición():
            return
        await asyncio.sleep(0.05)
    assert condición()


def teclas(dispositivo: dispositivo) -> list:
    return [a["key"] for a in dispositivo.listaAcciones]


class TestTeclaRepetida:
    def test_detecta_tecla_repetida(self):
        lista = [{"nombre": "a", "key": 1}, {"nombre": "b", "key": 2}]
        assert moduloTeclas.teclaRepetida(lista, 2) is lista[1]

    def test_tecla_libre(self):
        assert moduloTeclas.teclaRepetida([{"nombre": "a", "key": 1}], 3) is None

    def test_numero_y_texto_son_la_misma_tecla(self):
        lista = [{"nombre": "a", "key": 5}]
        assert moduloTeclas.teclaRepetida(lista, "5") is lista[0]

    def test_editar_no_choca_consigo_misma(self):
        lista = [{"nombre": "a", "key": 1}, {"nombre": "b", "key": 2}]
        assert moduloTeclas.teclaRepetida(lista, 1, ignorar=lista[0]) is None

    def test_editar_detecta_otra_accion(self):
        lista = [{"nombre": "a", "key": 1}, {"nombre": "b", "key": 2}]
        assert moduloTeclas.teclaRepetida(lista, 2, ignorar=lista[0]) is lista[1]

    def test_ignorar_compara_por_identidad(self):
        # Una acción igual en contenido pero distinta en memoria sigue siendo repetida
        lista = [{"nombre": "a", "key": 1}]
        assert moduloTeclas.teclaRepetida(lista, 1, ignorar={"nombre": "a", "key": 1}) is lista[0]


class TestOrdenTecla:
    def test_numeros_antes_que_texto(self):
        lista = [{"key": "b"}, {"key": 10}, {"key": "a"}, {"key": 2}]
        lista.sort(key=moduloTeclas.ordenTecla)
        assert [a["key"] for a in lista] == [2, 10, "a", "b"]


class TestOrdenarAcciones:
    lista = [{"nombre": "b", "key": 2, "accion": "os"}, {"nombre": "A", "key": 1, "accion": "escribir"}]

    def test_por_nombre_ignora_mayusculas(self):
        assert [a["nombre"] for a in moduloTeclas.ordenarAcciones(self.lista, "nombre")] == ["A", "b"]

    def test_por_accion_inverso(self):
        assert [a["accion"] for a in moduloTeclas.ordenarAcciones(self.lista, "accion", True)] == ["os", "escribir"]

    def test_no_modifica_lista_original(self):
        moduloTeclas.ordenarAcciones(self.lista, "key")
        assert self.lista[0]["key"] == 2


class TestClaseNavegacion:
    async def test_entra_y_sale_de_folder(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        assert gui.pestañas.claseNavegación(deck) == ""
        assert gui.pestañas.claseNavegación(deck) == "", "redibujar el mismo folder no anima"
        deck.folderActual = "obs/escenas"
        assert gui.pestañas.claseNavegación(deck) == "navega-entra"
        deck.folderActual = "/"
        assert gui.pestañas.claseNavegación(deck) == "navega-sale"

    async def test_pagina_siguiente_y_anterior(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        deck.paginaActual = lambda: 1
        gui.pestañas.claseNavegación(deck)
        deck.paginaActual = lambda: 2
        assert gui.pestañas.claseNavegación(deck) == "navega-entra"
        deck.paginaActual = lambda: 1
        assert gui.pestañas.claseNavegación(deck) == "navega-sale"


class TestPaginaAcciones:
    async def test_muestra_acciones_y_cabecera(self, user: User, gui: miGui):
        await user.open("/")
        await user.should_see("Uno")
        await user.should_see("Dos")
        await user.should_see("Escribir texto")
        assert user.find(marker="cabecera-folder").elements.pop().text == "/"
        await user.should_see(marker="editar-deck-1")

    async def test_lista_no_muestra_propiedad_folder(self, user: User, gui: miGui, deck: dispositivoFalso):
        deck.listaAcciones.append(dataAccion(key="propiedad_folder", imagenOpciones={"fondo": "#00ff00"}))
        await user.open("/")
        await user.should_see(marker="editar-deck-1")
        await user.should_not_see(marker="editar-deck-propiedad_folder")

    async def test_agregar_accion(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        await llenarFormulario(user, "Tres", "3", "Escribir texto", Texto="adios")
        user.find(marker="botonAgregar").click()

        await user.should_see("Tres agregada en deck, tecla 3")
        nueva = deck.listaAcciones[-1]
        assert nueva.aDict() == {"nombre": "Tres", "key": 3, "accion": "escribir", "opciones": {"texto": "adios"}}
        assert deck.vecesSalvado == 1
        await user.should_see(marker="editar-deck-3")

    async def test_agregar_accion_con_descripcion(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        await llenarFormulario(user, "Tres", "3", "Escribir texto", Texto="adios")
        user.find(marker="editor-descripcion").type("Escribe adios")
        user.find(marker="botonAgregar").click()

        await user.should_see("Tres agregada en deck, tecla 3")
        assert deck.listaAcciones[-1].descripcion == "Escribe adios"
        assert gui.formulario.editoresData["nombre"].value == ""

    async def test_agregar_ordena_por_tecla(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        await llenarFormulario(user, "Cero", "0", "Delay", Tiempo="1")
        user.find(marker="botonAgregar").click()
        assert teclas(deck) == [0, 1, 2]

    async def test_tecla_repetida_no_se_guarda(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        await llenarFormulario(user, "Otra", "1", "Escribir texto", Texto="x")
        user.find(marker="botonAgregar").click()

        await user.should_see("La tecla 1 ya la usa 'Uno', elige otra")
        assert teclas(deck) == [1, 2]
        assert deck.vecesSalvado == 0
        assert gui.formulario.editoresData["nombre"].value == "Otra", "el formulario no se limpia para poder corregir"

    @pytest.mark.parametrize(
        "campos, mensaje",
        [
            ({}, "Falta Nombre"),
            ({"nombre": "A"}, "Falta Tecla"),
            ({"nombre": "A", "tecla": "9"}, "Falta elegir la acción"),
            ({"nombre": "A", "tecla": "x", "acción": "Delay"}, "En deck la tecla es un número"),
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
        await user.should_see("Falta Texto")
        assert gui.formulario.opcionesEditar["Texto"].props["error-message"] == "Falta Texto", "el error se marca en el campo"
        assert deck.vecesSalvado == 0

    async def test_editar_llena_formulario(self, user: User, gui: miGui):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        assert gui.formulario.botonAgregar.icon == "save" and gui.formulario.tooltipAgregar.text == "Guardar cambios"
        assert gui.formulario.editoresData["nombre"].value == "Uno"
        assert gui.formulario.editoresData["key"].value == 1
        assert gui.formulario.editorAcción.value == "Escribir texto"
        assert gui.formulario.opcionesEditar["Texto"].value == "hola"

    async def test_cambiar_accion_mantiene_propiedades(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        await llenarFormulario(user, acción="Pegar texto")
        assert gui.formulario.opcionesEditar["Texto"].value == "hola"

        user.find(marker="botonAgregar").click()
        await user.should_see("Uno guardada en deck, tecla 1")
        assert deck.listaAcciones[0]["accion"] == "pegar"
        assert deck.listaAcciones[0]["opciones"] == {"texto": "hola"}

    async def test_editar_otra_accion_no_arrastra_valores(self, user: User, gui: miGui, deck: dispositivoFalso):
        deck.listaAcciones.append(dataAccion.desdeDict({"nombre": "Tres", "key": 3, "accion": "pegar", "opciones": {}}))
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        user.find(marker="editar-deck-3").click()
        assert gui.formulario.opcionesEditar["Texto"].value in ("", None)

    async def test_opcion_invalida_no_cambia_la_accion(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        await llenarFormulario(user, nombre="Uno editado")
        user.find(marker="opción-Texto").clear()
        user.find(marker="botonAgregar").click()

        await user.should_see("Falta Texto")
        assert deck.listaAcciones[0]["nombre"] == "Uno", "si otro guardado escribe el .md no debe llevar la edición a medias"
        assert deck.vecesSalvado == 0

    async def test_editar_misma_tecla(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        await llenarFormulario(user, nombre="Uno editado", Texto="chao")
        user.find(marker="botonAgregar").click()

        await user.should_see("Uno editado guardada en deck, tecla 1")
        assert len(deck.listaAcciones) == 2
        assert deck.listaAcciones[0]["nombre"] == "Uno editado"
        assert deck.listaAcciones[0]["opciones"] == {"texto": "chao"}
        assert deck.vecesSalvado == 1
        assert gui.formulario.botonAgregar.icon == "add" and gui.formulario.tooltipAgregar.text == "Agregar acción"

    async def test_botones_al_editar(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        assert not gui.formulario.botonEjecutar.visible and not gui.formulario.botonBorrar.visible
        cantidad = len(deck.listaAcciones)
        acción = deck.listaAcciones[0]
        user.find(marker=f"editar-deck-{acción.key}").click()
        assert gui.formulario.botonEjecutar.visible and gui.formulario.botonBorrar.visible

        gui.ejecutarAcción = MagicMock()
        user.find(marker="botonEjecutar").click()
        assert gui.ejecutarAcción.call_args_list == [((acción,),), ((acción, False),)], "presiona y suelta"

        user.find(marker="botonBorrar").click()
        assert acción not in deck.listaAcciones and len(deck.listaAcciones) == cantidad - 1
        assert gui.formulario.accionEditar is None and not gui.formulario.botonBorrar.visible

    async def test_editar_a_tecla_ocupada(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        await llenarFormulario(user, tecla="2")
        user.find(marker="botonAgregar").click()

        await user.should_see("La tecla 2 ya la usa 'Dos', elige otra")
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
        assert gui.formulario.botonAgregar.icon == "add" and gui.formulario.tooltipAgregar.text == "Agregar acción"
        assert gui.formulario.accionEditar is None
        assert gui.formulario.editoresData["nombre"].value == ""

    async def test_borrar_accion(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="borrar-deck-2").click()
        assert teclas(deck) == [1]
        assert deck.vecesSalvado == 1
        await user.should_not_see(marker="editar-deck-2")

    async def test_deshacer_borrar(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        primera = deck.listaAcciones[0]
        user.find(marker="borrar-deck-1").click()
        assert teclas(deck) == [2]
        with user:
            gui.deshacerBorrar(gui.contadorBorrados)
        assert deck.listaAcciones[0] is primera, "vuelve a su posición"
        assert deck.vecesSalvado == 2
        await user.should_see(marker="editar-deck-1")
        with user:
            gui.deshacerBorrar(gui.contadorBorrados)
        assert teclas(deck) == [1, 2], "deshacer dos veces no duplica"

    async def test_deshacer_borrar_en_otro_folder(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="borrar-deck-2").click()
        deck.folderActual = "/otro"
        with user:
            gui.deshacerBorrar(gui.contadorBorrados)
        assert teclas(deck) == [1] and deck.vecesSalvado == 1
        await user.should_see("No se pudo deshacer")

    async def test_ejecutar_accion(self, user: User, gui: miGui, deck: dispositivoFalso):
        gui.ejecutarAcción = MagicMock()
        await user.open("/")
        user.find(marker="ejecutar-deck-2").click()
        assert gui.ejecutarAcción.call_args_list[0] == ((deck.listaAcciones[1],),)


class TestFormularioSeguro:
    async def test_cambiar_de_tecla_pregunta_si_hay_cambios(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        assert gui.formulario.tituloFormulario.text == "Editando 'Uno' · deck · tecla 1"
        user.find(marker="editar-deck-2").click()
        assert gui.formulario.editoresData["nombre"].value == "Dos", "sin cambios no pregunta"

        await llenarFormulario(user, nombre="Dos cambiado")
        user.find(marker="editar-deck-1").click()
        assert gui.formulario.editoresData["nombre"].value == "Dos cambiado", "con cambios espera la respuesta"
        await user.should_see("Hay cambios sin guardar en 'Dos'. ¿Descartarlos?")
        clickEnDialogoAbierto(user, "Descartar")
        assert gui.formulario.editoresData["nombre"].value == "Uno"

    async def test_guarda_numero_bool_y_yaml_con_su_tipo(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        await llenarFormulario(user, "Tres", "3", "Escribir texto", Texto="hola")
        with user:
            gui.formulario.opcionesEditar["Velocidad"].value = 0.5
        user.find(marker="botonAgregar").click()
        assert deck.listaAcciones[-1]["opciones"] == {"texto": "hola", "intervalo": 0.5}

        await llenarFormulario(user, "Cuatro", "4", "Presiona", Presionado="accion: delay", Soltar="[1, 2]")
        user.find(marker="botonAgregar").click()
        await user.should_see("Soltar: debe ser diccionario en YAML")
        assert deck.vecesSalvado == 1

        user.find(marker="opción-Soltar").clear().type("accion: delay")
        user.find(marker="botonAgregar").click()
        assert deck.listaAcciones[-1]["opciones"] == {"presionado": {"accion": "delay"}, "soltar": {"accion": "delay"}}, "Estado (bool) en su valor por defecto no se guarda"

    async def test_editar_muestra_yaml_y_numero(self, user: User, gui: miGui, deck: dispositivoFalso):
        deck.listaAcciones.append(dataAccion.desdeDict({"nombre": "P", "key": 5, "accion": "presionar", "opciones": {"presionado": {"accion": "delay"}}}))
        deck.listaAcciones.append(dataAccion.desdeDict({"nombre": "E", "key": 6, "accion": "escribir", "opciones": {"texto": "x", "intervalo": "rápido"}}))
        await user.open("/")
        user.find(marker="editar-deck-5").click()
        assert gui.formulario.opcionesEditar["Presionado"].value == "accion: delay\n"
        user.find(marker="editar-deck-6").click()
        assert gui.formulario.opcionesEditar["Velocidad"].value is None
        assert gui.formulario.opcionesEditar["Velocidad"].props["error"], "valor viejo inválido se marca"

    async def test_perder_foco_suelta_las_teclas(self, user: User, gui: miGui, deck: dispositivoFalso, monkeypatch):
        monkeypatch.setattr(moduloMiGui, "SalvarValor", MagicMock())
        gui.ejecutarAcción = MagicMock()
        await user.open("/")
        with user:
            gui.cambiarModo(True)
        user.find(marker="tecla-deck-1").trigger("pointerdown")
        with user:
            gui.soltarTodas()
            gui.soltarTodas()
        assert gui.ejecutarAcción.call_args_list == [((deck.listaAcciones[0],),), ((deck.listaAcciones[0], False),)]


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
        clickEnDialogoAbierto(user, item)
        gui.ejecutarAccionSistema.assert_called_once_with(comando)

    async def test_cancelar_no_ejecuta(self, user: User, gui: miGui):
        gui.ejecutarAccionSistema = MagicMock()
        await user.open("/")
        user.find(marker="menu-Salir").click()
        clickEnDialogoAbierto(user, "Cancelar")
        gui.ejecutarAccionSistema.assert_not_called()

    @pytest.mark.parametrize("item, ruta", [("Módulos", "/modulos"), ("Dispositivos", "/dispositivos"), ("Configurar", "/configurar"), ("Acciones", "/")])
    async def test_navegar(self, user: User, gui: miGui, monkeypatch, item, ruta):
        monkeypatch.setattr(moduloMiGui, "leerData", lambda _: {})
        monkeypatch.setattr(configuracion, "leerData", lambda _: {})
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


class TestConfigurar:
    async def test_switch_autoarranque(self, user: User, gui: miGui, monkeypatch, tmp_path):
        from elGarrobo import servicio

        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(servicio.subprocess, "run", MagicMock())
        inicio = tmp_path / ".config/autostart/elgarrobo.desktop"

        await user.open("/configurar")
        user.find(marker="autoarranque").click()
        assert inicio.exists()
        assert (tmp_path / ".config/systemd/user/elgarrobo.service").exists()

        user.find(marker="autoarranque").click()
        assert not inicio.exists()

    async def test_cambiar_tema(self, user: User, gui: miGui, monkeypatch):
        salvar = MagicMock()
        monkeypatch.setattr(moduloMiGui, "SalvarValor", salvar)
        await user.open("/configurar")
        oscuro = next(iter(user.find(kind=ui.dark_mode).elements))
        assert oscuro.value is True, "por defecto oscuro, como antes de tener temas"

        selector = next(iter(user.find(marker="tema").elements))
        for nombreTema, valor in (("claro", False), ("auto", None)):
            with user:
                selector.value = nombreTema
            assert oscuro.value is valor
            salvar.assert_called_with(moduloMiGui.ARCHIVO_PREFERENCIAS, "tema", nombreTema)

        await user.open("/")
        assert next(iter(user.find(kind=ui.dark_mode).elements)).value is None, "las otras páginas abren con el tema elegido"


class TestActivables:
    @pytest.mark.parametrize("ruta, archivo", [("/modulos", "modulos"), ("/dispositivos", "dispositivos")])
    async def test_switch_guarda_estado(self, user: User, gui: miGui, monkeypatch, ruta, archivo):
        salvar = MagicMock()
        monkeypatch.setattr(configuracion, "leerData", lambda _: {})
        monkeypatch.setattr(configuracion, "SalvarValor", salvar)
        await user.open(ruta)
        await user.should_see("se aplica al reiniciar ElGarrobo")
        await user.should_not_see(marker="reiniciar-pendiente")

        switch = next(iter(user.find(kind=ui.switch).elements))
        with user:
            switch.value = True
        assert salvar.call_args.args[0] == archivo
        assert salvar.call_args.args[2] is True
        await user.should_see("se activará al reiniciar ElGarrobo")
        await user.should_see(marker="reiniciar-pendiente")
        await user.should_see("Pendiente de reinicio")

        with user:
            switch.value = False
        await user.should_see("como estaba")
        await user.should_not_see(marker="reiniciar-pendiente")

    async def test_pendiente_sigue_en_acciones_y_reinicia(self, user: User, gui: miGui, monkeypatch):
        monkeypatch.setattr(configuracion, "leerData", lambda _: {})
        monkeypatch.setattr(configuracion, "SalvarValor", MagicMock())
        gui.ejecutarAccionSistema = MagicMock()
        await user.open("/dispositivos")
        with user:
            next(iter(user.find(kind=ui.switch).elements)).value = True

        await user.open("/")
        user.find(marker="reiniciar-pendiente").click()
        clickEnDialogoAbierto(user, "Reiniciar")
        gui.ejecutarAccionSistema.assert_called_once_with("reiniciar_app")

    async def test_la_gui_no_se_apaga_desde_dispositivos(self, user: User, gui: miGui, monkeypatch):
        monkeypatch.setattr(configuracion, "leerData", lambda _: {"gui": True})
        await user.open("/dispositivos")
        await user.should_see("Pedal StreamDeck")
        await user.should_not_see("Interfaz Gráfica")

    def test_gui_forzada_con_g(self, monkeypatch):
        from elGarrobo import elGarrobo as moduloElGarrobo

        monkeypatch.setattr(moduloElGarrobo, "leerData", lambda archivo: {} if archivo == "modulos" else {"gui": False})
        app = moduloElGarrobo.elGarrobo.__new__(moduloElGarrobo.elGarrobo)
        app.cargarClasesModulos = MagicMock()
        app.iniciarModulo(gui=True)
        assert app.dispositivos["gui"] is True and app.ModuloGui is True


class TestConfiguracionModulos:
    @pytest.fixture
    def archivos(self, monkeypatch) -> dict:
        """Archivos de configuración en memoria: lo que se guarda queda en el dict"""
        archivos = {}
        monkeypatch.setattr(configuracion, "leerData", lambda _: {})
        monkeypatch.setattr(configuracion, "ObtenerArchivo", lambda archivo: archivos.get(archivo))
        monkeypatch.setattr(configuracion, "SalvarArchivo", lambda archivo, data: archivos.update({archivo: data}))
        return archivos

    @staticmethod
    def elemento(user: User, marca: str) -> ui.element:
        return next(iter(user.find(marker=marca).elements))

    async def test_sin_archivo_muestra_valor_por_defecto(self, user: User, gui: miGui, archivos: dict):
        await user.open("/modulos")

        assert self.elemento(user, "config-estado_pc-nombre_pc").value == "pc-default"
        assert self.elemento(user, "config-estado_fdm_monster-intervalo_segundos").value == 30
        user.find(marker="config-estado_pc-nombre_pc").clear().type("ryuk")
        user.find(marker="guardar-estado_pc").click()

        await user.should_see("guardado; se aplica al reiniciar ElGarrobo")
        await user.should_see(marker="reiniciar-pendiente")
        assert gui.pendientesReinicio == {"modulos/estado_pc.md": "opciones de estadoPc"}
        assert archivos["modulos/estado_pc.md"] == {"nombre_pc": "ryuk"}

    async def test_edita_agrega_y_quita_impresoras(self, user: User, gui: miGui, archivos: dict):
        archivos["modulos/estado_octoprint.md"] = {
            "impresoras": [{"nombre": "Ender", "url": "http://a", "token": "secreto", "intervalo_segundos": 30}],
            "extra": "se conserva",
        }
        await user.open("/modulos")

        assert self.elemento(user, "config-estado_octoprint-0-token").props.get("type") == "password"
        user.find(marker="config-estado_octoprint-0-url").clear().type("http://b")
        with user:
            self.elemento(user, "config-estado_octoprint-0-intervalo_segundos").value = 60

        user.find(marker="agregar-estado_octoprint-impresoras").click()
        await user.should_see(marker="config-estado_octoprint-1-nombre")  # refresh se dibuja en el siguiente ciclo
        assert self.elemento(user, "config-estado_octoprint-1-intervalo_segundos").value == 30, "nueva con defectos"
        user.find(marker="config-estado_octoprint-1-nombre").type("Prusa")
        user.find(marker="config-estado_octoprint-1-url").type("http://c")
        user.find(marker="config-estado_octoprint-1-token").type("otro")
        user.find(marker="guardar-estado_octoprint").click()

        await user.should_see("guardado; se aplica al reiniciar ElGarrobo")
        impresoras = archivos["modulos/estado_octoprint.md"]["impresoras"]
        assert impresoras[0] == {"nombre": "Ender", "url": "http://b", "token": "secreto", "intervalo_segundos": 60}
        assert type(impresoras[0]["intervalo_segundos"]) is int
        assert impresoras[1]["nombre"] == "Prusa" and impresoras[1]["intervalo_error_segundos"] == 120
        assert archivos["modulos/estado_octoprint.md"]["extra"] == "se conserva"

        user.find(marker="quitar-estado_octoprint-0").click()
        await user.should_not_see(marker="config-estado_octoprint-1-nombre")
        user.find(marker="guardar-estado_octoprint").click()
        assert [i["nombre"] for i in archivos["modulos/estado_octoprint.md"]["impresoras"]] == ["Prusa"]

    async def test_obligatorio_vacio_no_guarda(self, user: User, gui: miGui, archivos: dict):
        await user.open("/modulos")

        user.find(marker="agregar-estado_klipper-impresoras").click()
        await user.should_see(marker="config-estado_klipper-0-url")
        user.find(marker="guardar-estado_klipper").click()

        await user.should_see("Faltan valores obligatorios")
        assert "modulos/estado_klipper.md" not in archivos
        assert self.elemento(user, "config-estado_klipper-0-url").props["error-message"] == "Obligatorio"

    async def test_campo_vacio_usa_defecto_del_modulo(self, user: User, gui: miGui, archivos: dict):
        archivos["modulos/estado_klipper.md"] = {"impresoras": [{"nombre": "U1", "topic": "u1", "url": "http://k"}]}
        await user.open("/modulos")

        user.find(marker="config-estado_klipper-0-topic").clear()
        user.find(marker="guardar-estado_klipper").click()

        assert archivos["modulos/estado_klipper.md"]["impresoras"][0] == {"nombre": "U1", "url": "http://k"}

class TestEditorApariencia:
    async def test_editor_boton_guarda_titulo_y_fondo(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        user.find(marker="botonEditarBoton").click()
        user.find(marker="editor-titulo").clear().type("Hola")
        gui.formulario.editorFondo.value = "#2b7a10"  # ponytail: el simulador no escribe en color_input
        user.find(marker="botonListoBoton").click()
        user.find(marker="botonAgregar").click()

        await user.should_see("Uno guardada en deck, tecla 1")
        assert deck.listaAcciones[0].titulo == "Hola"
        assert deck.listaAcciones[0].aDict()["imagen_opciones"] == {"fondo": "#2b7a10"}

        user.find(marker="editar-deck-1").click()
        assert gui.formulario.editorFondo.value == "#2b7a10"


    async def test_editor_sin_apariencia_usa_nombre_como_titulo(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        user.find(marker="botonEditarBoton").click()
        assert gui.formulario.editorTitulo.value == deck.listaAcciones[0].nombre

        user.find(marker="editor-titulo").clear().type("Hola")
        user.find(marker="botonListoBoton").click()
        user.find(marker="botonEditarBoton").click()
        assert gui.formulario.editorTitulo.value == "Hola", "con apariencia no se reemplaza el título"

    async def test_editor_boton_guarda_topico_mqtt_del_titulo(self, user: User, gui: miGui, deck: dispositivoFalso):
        deck.listaAcciones[0].tituloOpciones = {"color": "blue"}
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        user.find(marker="botonEditarBoton").click()
        user.find(marker="editor-titulo-mqtt").type("estado/progreso")
        user.find(marker="botonListoBoton").click()
        user.find(marker="botonAgregar").click()
        assert deck.listaAcciones[0].tituloOpciones == {"color": "blue", "mqtt": "estado/progreso"}

        user.find(marker="editar-deck-1").click()
        assert gui.formulario.editorTituloMQTT.value == "estado/progreso"
        user.find(marker="botonEditarBoton").click()
        user.find(marker="editor-titulo-mqtt").clear()
        user.find(marker="botonListoBoton").click()
        user.find(marker="botonAgregar").click()
        assert deck.listaAcciones[0].tituloOpciones == {"color": "blue"}, "vacío quita el tópico sin tocar las otras opciones"

    async def test_vista_previa_dibuja_fondo(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="editar-deck-1").click()
        user.find(marker="botonEditarBoton").click()
        gui.formulario.editorFondo.value = "#ff0000"

        assert gui.formulario.vistaPrevia.visible
        assert isinstance(gui.formulario.vistaPrevia.source, Image.Image)
        assert gui.formulario.vistaPrevia.source.convert("RGB").getpixel((1, 1)) == (255, 0, 0)
        assert deck.listaAcciones[0].fondo is None, "la vista previa no guarda"


    async def test_editar_carga_fondo_sin_borrarlo(self, user: User, gui: miGui, deck: dispositivoFalso):
        deck.listaAcciones[0].fondo = "#ff8000"
        await user.open("/")
        user.find(marker="editar-deck-1").click()

        assert gui.formulario.editorFondo.value == "#ff8000"
        assert deck.listaAcciones[0].fondo == "#ff8000", "la vista previa no debe modificar la acción"



@pytest.fixture
def pedal() -> MiPedal:
    pedal = MiPedal({"nombre": "pedal"})
    pedal._listaAcciones = pedal.convertirAcciones(
        [
            {"nombre": "Uno", "key": 1, "accion": "escribir", "opciones": {"texto": "hola"}},
            {"nombre": "Cinco", "key": 5, "accion": "escribir", "opciones": {"texto": "cinco"}},
        ]
    )
    pedal.salvarAcciones = lambda: None
    return pedal


@pytest.fixture
def guiPedal(user: User, pedal: MiPedal) -> miGui:
    gui = miGui({"nombre": "gui"})
    gui.listaClasesAcciones = cargarClasesAcciones()
    gui.listaDispositivos = [pedal]
    return gui


class TestCuadricula:
    async def test_muestra_los_pedales_de_la_pagina(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        await user.should_see(marker="tecla-pedal-1")
        await user.should_see(marker="tecla-pedal-3")
        await user.should_see("Página 1")
        assert not next(iter(user.find(marker="paginaAnterior-pedal").elements)).enabled
        assert next(iter(user.find(marker="paginaSiguiente-pedal").elements)).enabled
        await user.should_not_see(marker="tecla-pedal-4")

    async def test_click_en_boton_edita_la_accion(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        user.find(marker="tecla-pedal-1").click()
        assert guiPedal.formulario.editoresData["nombre"].value == "Uno"
        assert guiPedal.formulario.dispositivoEditar is pedal

    async def test_click_en_vacio_prepara_la_tecla(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        user.find(marker="tecla-pedal-2").click()
        assert guiPedal.formulario.editoresData["key"].value == 2
        assert guiPedal.formulario.editoresData["nombre"].value == ""
        assert guiPedal.formulario.dispositivoEditar is pedal

    async def test_cambiar_pagina_mueve_el_pedal(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        user.find(marker="paginaSiguiente-pedal").click()
        await user.should_see("Página 2")
        assert next(iter(user.find(marker="paginaAnterior-pedal").elements)).enabled
        await user.should_see(marker="tecla-pedal-5")
        assert pedal.desfaseTeclas == 3
        user.find(marker="paginaSiguiente-pedal").click()
        await user.should_see("Página 3")
        assert not next(iter(user.find(marker="paginaSiguiente-pedal").elements)).enabled, "editando solo hay una página vacía extra"

    async def test_interruptor_a_lista(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        with user:
            guiPedal.pestañas.cambiarVista(pedal, True)
        await user.should_see(marker="orden-key-pedal")
        await user.should_not_see(marker="tecla-pedal-1")

    async def test_duplicar_accion(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        user.find(marker="duplicar-pedal").click()
        user.find(marker="tecla-pedal-2").click()
        assert len(pedal.listaAcciones) == 2, "sin acción elegida la tecla vacía no hace nada"

        user.find(marker="tecla-pedal-1").click()
        user.find(marker="tecla-pedal-2").click()
        user.find(marker="tecla-pedal-3").click()
        assert sorted(a.key for a in pedal.listaAcciones if a.nombre == "Uno") == [1, 2, 3], "sigue elegida para pegar varias veces"
        copia = next(a for a in pedal.listaAcciones if a.key == 2)
        assert copia is not pedal.listaAcciones[0] and copia.opciones is not pedal.listaAcciones[0].opciones

        user.find(marker="duplicar-pedal").click()
        user.find(marker="tecla-pedal-2").click()
        assert guiPedal.formulario.editoresData["nombre"].value == "Uno", "fuera del modo vuelve a editar"

    async def test_intercambiar_teclas(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        user.find(marker="intercambiar-pedal").click()
        user.find(marker="tecla-pedal-1").click()
        user.find(marker="tecla-pedal-2").click()
        assert [a.key for a in pedal.listaAcciones if a.nombre == "Uno"] == [2], "a tecla vacía se mueve"

        user.find(marker="tecla-pedal-2").click()
        user.find(marker="tecla-pedal-3").click()
        user.find(marker="tecla-pedal-3").click()
        user.find(marker="tecla-pedal-3").click()
        assert [a.key for a in pedal.listaAcciones if a.nombre == "Uno"] == [3], "misma tecla dos veces no cambia nada"

        pedal.listaAcciones[-1].key = 2  # Cinco a la página visible
        user.find(marker="tecla-pedal-2").click()
        user.find(marker="tecla-pedal-3").click()
        assert {a.nombre: a.key for a in pedal.listaAcciones} == {"Uno": 2, "Cinco": 3}

        user.find(marker="intercambiar-pedal").click()
        user.find(marker="tecla-pedal-2").click()
        assert guiPedal.formulario.editoresData["nombre"].value == "Uno", "fuera del modo vuelve a editar"

    async def test_modos_marcan_sin_redibujar(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        tecla = lambda n: next(iter(user.find(marker=f"tecla-pedal-{n}").elements))
        uno = tecla(1)
        anillo = f"ring-{tema.colorActivo}"
        intercambiar = next(iter(user.find(marker="intercambiar-pedal").elements))

        user.find(marker="intercambiar-pedal").click()
        assert f"bg-{tema.colorActivo}" in intercambiar.classes and intercambiar.props["aria-pressed"] == "true"
        user.find(marker="tecla-pedal-1").click()
        assert tecla(1) is uno and anillo in uno.classes, "activar el modo y elegir solo marcan, no redibujan"

        user.find(marker="duplicar-pedal").click()
        assert anillo not in uno.classes and f"bg-{tema.colorBotones}" in intercambiar.classes
        user.find(marker="tecla-pedal-1").click()
        assert tecla(1) is uno and anillo in uno.classes

        user.find(marker="tecla-pedal-2").click()
        assert tecla(1) is not uno, "pegar cambia las teclas y redibuja"


class TestModoUsar:
    @pytest.fixture(autouse=True)
    def salvar(self, monkeypatch) -> MagicMock:
        salvar = MagicMock()
        monkeypatch.setattr(moduloMiGui, "SalvarValor", salvar)
        return salvar

    async def test_click_ejecuta_sin_editar(self, user: User, guiPedal: miGui, pedal: MiPedal, salvar: MagicMock):
        guiPedal.ejecutarAcción = MagicMock()
        await user.open("/")
        with user:
            guiPedal.cambiarModo(True)
        salvar.assert_called_once_with(moduloMiGui.ARCHIVO_PREFERENCIAS, "modo_usar", True)
        await user.should_not_see(marker="intercambiar-pedal")
        await user.should_not_see(marker="propiedadesFolder-pedal")

        user.find(marker="tecla-pedal-1").trigger("pointerdown")
        guiPedal.ejecutarAcción.assert_called_once_with(pedal.listaAcciones[0])
        assert guiPedal.formulario.editoresData["nombre"].value == "", "en Usar no abre el formulario"
        await user.should_see(marker="ultimaAcción")
        assert guiPedal.ultimaLabel.text == "Uno"

    async def test_volver_a_editar_conserva_formulario(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        user.find(marker="tecla-pedal-1").click()
        with user:
            guiPedal.cambiarModo(True)
            guiPedal.cambiarModo(False)
        assert guiPedal.formulario.editoresData["nombre"].value == "Uno"
        await user.should_see(marker="intercambiar-pedal")

    async def test_sin_cuadricula_muestra_botonera(self, user: User, gui: miGui, deck: dispositivoFalso):
        gui.ejecutarAcción = MagicMock()
        await user.open("/")
        with user:
            gui.cambiarModo(True)
        await user.should_not_see(marker="editar-deck-1")
        user.find(marker="tecla-deck-2").trigger("pointerdown")
        gui.ejecutarAcción.assert_called_once_with(deck.listaAcciones[1])

    async def test_error_al_ejecutar_avisa(self, user: User, gui: miGui, deck: dispositivoFalso):
        gui.ejecutarAcción = MagicMock(side_effect=RuntimeError("sin OBS"))
        await user.open("/")
        with user:
            gui.cambiarModo(True)
        user.find(marker="tecla-deck-1").trigger("pointerdown")
        await user.should_see("No se pudo ejecutar Uno: sin OBS")

    async def test_mantener_presiona_y_suelta_una_vez(self, user: User, guiPedal: miGui, pedal: MiPedal):
        guiPedal.ejecutarAcción = MagicMock()
        await user.open("/")
        with user:
            guiPedal.cambiarModo(True)
        tecla = user.find(marker="tecla-pedal-1")
        tecla.trigger("pointerleave")
        assert guiPedal.ejecutarAcción.call_count == 0, "salir sin presionar no manda soltar"

        tecla.trigger("keydown.enter").trigger("keydown.enter")
        tecla.trigger("keyup.enter").trigger("pointerleave")
        uno = pedal.listaAcciones[0]
        assert guiPedal.ejecutarAcción.call_args_list == [((uno,),), ((uno, False),)], "una vez presionar y una vez soltar"



@pytest.fixture
def plus() -> MiDeckCombinado:
    plus = MiDeckCombinado({"nombre": "plus", "streamDecksPlus": [{"id": 0, "nombre": "Plus"}]})
    plus._listaAcciones = plus.convertirAcciones(
        [
            {"nombre": "Uno", "key": 1, "accion": "escribir", "opciones": {"texto": "hola"}},
            {"nombre": "Mute", "key": "dial_1", "accion": "escribir", "opciones": {"texto": "m"}},
            {"nombre": "Pantalla", "key": "touchscreen_1", "accion": "escribir", "opciones": {"texto": "t"}},
        ]
    )
    plus.accionesCargadas()
    plus.listaDeck[0].baseTeclas = 1  # la asigna conectar()
    plus.salvarAcciones = lambda: None
    return plus


@pytest.fixture
def guiPlus(user: User, plus: MiDeckCombinado) -> miGui:
    gui = miGui({"nombre": "gui"})
    gui.listaClasesAcciones = cargarClasesAcciones()
    gui.listaDispositivos = [plus]
    return gui


class TestStreamDeckPlus:
    async def test_dibuja_teclas_pantalla_y_perillas(self, user: User, guiPlus: miGui):
        await user.open("/")
        await user.should_see(marker="tecla-plus-8")
        await user.should_not_see(marker="tecla-plus-9"), "desconectado se dibuja 2x4"
        await user.should_see(marker="tecla-plus-touchscreen_1")
        await user.should_see(marker="tecla-plus-touchscreen_2"), "en Editar hay una zona vacía para agregar"
        await user.should_see(marker="tecla-plus-deslizar_derecha_1")
        await user.should_see(marker="tecla-plus-dial_4")
        await user.should_see(marker="tecla-plus-dial_izquierdo_1")
        await user.should_not_see(marker="tecla-plus-dial_5")

    async def test_click_edita_y_prepara_controles(self, user: User, guiPlus: miGui, plus: MiDeckCombinado):
        await user.open("/")
        user.find(marker="tecla-plus-dial_1").click()
        assert guiPlus.formulario.editoresData["nombre"].value == "Mute"
        user.find(marker="botonLimpiar").click()
        user.find(marker="tecla-plus-dial_derecho_2").click()
        assert guiPlus.formulario.editoresData["key"].value == "dial_derecho_2"

    async def test_guardar_control_del_plus(self, user: User, guiPlus: miGui, plus: MiDeckCombinado):
        await user.open("/")
        user.find(marker="tecla-plus-touchscreen_2").click()
        await llenarFormulario(user, nombre="Zona dos", acción="Escribir texto", Texto="dos")
        user.find(marker="botonAgregar").click()
        assert any(a.key == "touchscreen_2" and a.nombre == "Zona dos" for a in plus.listaAcciones)

    async def test_tecla_invalida_en_plus(self, user: User, guiPlus: miGui, plus: MiDeckCombinado):
        await user.open("/")
        seleccionarPestaña(user, guiPlus, "plus")
        await llenarFormulario(user, nombre="Mal", tecla="dial", acción="Escribir texto", Texto="x")
        user.find(marker="botonAgregar").click()
        await user.should_see("o un control del Plus")
        assert len(plus.listaAcciones) == 3

    async def test_usar_ejecuta_perilla(self, user: User, guiPlus: miGui, plus: MiDeckCombinado):
        guiPlus.ejecutarAcción = MagicMock()
        await user.open("/")
        with user:
            guiPlus.cambiarModo(True)
        await user.should_not_see(marker="tecla-plus-touchscreen_2"), "en Usar no hay zona para agregar"
        user.find(marker="tecla-plus-dial_1").trigger("pointerdown")
        guiPlus.ejecutarAcción.assert_called_once_with(plus.listaAcciones[1])
        assert not next(iter(user.find(marker="tecla-plus-dial_2").elements)).enabled, "perilla sin acción apagada"


@pytest.fixture
def teclado() -> MiTecladoMacro:
    teclado = MiTecladoMacro({"nombre": "teclado", "distribucion": "ingles_87k"})
    teclado._listaAcciones = teclado.convertirAcciones([{"nombre": "Escena", "key": "KEY_A", "accion": "escribir", "opciones": {"texto": "a"}}])
    teclado.salvarAcciones = lambda: None
    return teclado


@pytest.fixture
def guiTeclado(user: User, teclado: MiTecladoMacro) -> miGui:
    gui = miGui({"nombre": "gui"})
    gui.listaClasesAcciones = cargarClasesAcciones()
    gui.listaDispositivos = [teclado]
    return gui


class TestDistribucionTeclado:
    def test_distribuciones_con_keycodes_validos(self):
        from evdev import ecodes

        for archivo in folderDistribuciones.glob("*.json"):
            teclas = [t["key"] for t in MiTecladoMacro({"nombre": "t", "distribucion": archivo.stem}).distribucionTeclas()]
            assert len(teclas) == len(set(teclas)), f"{archivo.name} repite teclas"
            assert all(t in ecodes.ecodes for t in teclas), f"{archivo.name} tiene keycodes inválidos"

    async def test_dibuja_y_edita(self, user: User, guiTeclado: miGui, teclado: MiTecladoMacro):
        await user.open("/")
        await user.should_see(marker="tecla-teclado-KEY_ESC")
        user.find(marker="tecla-teclado-KEY_A").click()
        assert guiTeclado.formulario.editoresData["nombre"].value == "Escena"
        user.find(marker="tecla-teclado-KEY_B").click()
        assert guiTeclado.formulario.editoresData["key"].value == "KEY_B"

    async def test_vista_previa_a_la_medida_de_la_tecla(self, user: User, guiTeclado: miGui, teclado: MiTecladoMacro):
        teclado.listaAcciones.append(dataAccion.desdeDict({"nombre": "Grabar", "key": "KEY_SPACE", "accion": "escribir", "titulo": "REC"}))
        await user.open("/")
        espacio = next(t for t in teclado.distribucionTeclas() if t["key"] == "KEY_SPACE")
        imagen = user.find(marker="tecla-teclado-KEY_SPACE").elements.pop().default_slot.children[0].source
        imagen = imagenVista(imagen)
        assert imagen.size == moduloTeclas.tamañoTecla(espacio) and imagen.width > imagen.height, "la barra espaciadora se dibuja ancha"
        user.find(marker="tecla-teclado-KEY_SPACE").click()
        guiTeclado.formulario.abrirEditorApariencia()
        assert guiTeclado.formulario.vistaPrevia.source.size == moduloTeclas.tamañoTecla(espacio)

    async def test_intercambiar(self, user: User, guiTeclado: miGui, teclado: MiTecladoMacro):
        await user.open("/")
        user.find(marker="intercambiar-teclado").click()
        user.find(marker="tecla-teclado-KEY_A").click()
        user.find(marker="tecla-teclado-KEY_F1").click()
        assert teclado.listaAcciones[0].key == "KEY_F1"

    async def test_teclas_fuera_de_la_distribucion(self, user: User, guiTeclado: miGui, teclado: MiTecladoMacro):
        teclado.listaAcciones.append(dataAccion.desdeDict({"nombre": "Capa Fn", "key": "KEY_F13", "accion": "escribir"}))
        await user.open("/")
        await user.should_see("Otras teclas")
        user.find(marker="tecla-teclado-KEY_F13").click()
        assert guiTeclado.formulario.editoresData["nombre"].value == "Capa Fn"

    async def test_cambiar_distribucion(self, user: User, guiTeclado: miGui, teclado: MiTecladoMacro, monkeypatch):
        moduloTeclado = sys.modules[MiTecladoMacro.__module__]
        guardado = {}
        monkeypatch.setattr(moduloTeclado, "ObtenerArchivo", lambda archivo: [{"nombre": "otro"}, {"nombre": "teclado", "distribucion": "ingles_87k"}])
        monkeypatch.setattr(moduloTeclado, "SalvarArchivo", lambda archivo, data: guardado.update({archivo: data}))
        await user.open("/")

        user.find(marker="distribucion-teclado").click()
        user.find(marker="opcionDistribucion-sonix_una_mano").click()
        assert teclado.distribucion == "sonix_una_mano"
        assert guardado["teclados.md"][1] == {"nombre": "teclado", "distribucion": "sonix_una_mano"}
        await user.should_see(marker="tecla-teclado-KEY_SPACE")

        user.find(marker="distribucion-teclado").click()
        user.find(marker="opcionDistribucion-None").click()
        assert guardado["teclados.md"] == [{"nombre": "otro"}, {"nombre": "teclado"}]
        await user.should_see(marker="orden-key-teclado")
        await user.should_see(marker="distribucion-teclado")

    async def test_elegir_distribucion_con_teclado(self, user: User, guiTeclado: miGui, teclado: MiTecladoMacro, monkeypatch):
        moduloTeclado = sys.modules[MiTecladoMacro.__module__]
        monkeypatch.setattr(moduloTeclado, "ObtenerArchivo", lambda archivo: [{"nombre": "teclado"}])
        monkeypatch.setattr(moduloTeclado, "SalvarArchivo", lambda archivo, data: None)
        await user.open("/")
        user.find(marker="distribucion-teclado").click()
        tarjeta = next(iter(user.find(marker="opcionDistribucion-sonix_una_mano").elements))
        assert tarjeta.props["role"] == "button" and tarjeta.props["tabindex"] == "0"
        user.find(marker="opcionDistribucion-sonix_una_mano").trigger("keydown.enter")
        assert teclado.distribucion == "sonix_una_mano"

    async def test_sin_distribucion_muestra_lista(self, user: User, guiTeclado: miGui, teclado: MiTecladoMacro):
        teclado.distribucion = "no_existe"
        await user.open("/")
        await user.should_see(marker="orden-key-teclado")



class TestAccionSinClase:
    async def test_editar_random_conserva_accion_y_pasos(self, user: User, gui: miGui, deck: dispositivoFalso):
        pasos = [{"accion": "teclas", "opciones": {"teclas": ["s"]}}]
        deck.listaAcciones.append(dataAccion.desdeDict({"nombre": "Azar", "key": 9, "accion": "random", "opciones": pasos}))
        await user.open("/")
        user.find(marker="editar-deck-9").click()

        assert gui.formulario.editorAcción.value == "random"
        assert "teclas" in gui.formulario.editorOpción.value

        user.find(marker="editor-nombre").clear().type("Azar 2")
        user.find(marker="botonAgregar").click()
        await user.should_see("Azar 2 guardada en deck, tecla 9")

        azar = deck.listaAcciones[-1]
        assert (azar.nombre, azar.accion, azar.opciones) == ("Azar 2", "random", pasos)


class TestAccionMacro:
    async def test_editar_macro_conserva_pasos_como_lista(self, user: User, gui: miGui, deck: dispositivoFalso):
        pasos = [{"accion": "teclas", "opciones": {"teclas": ["s"]}}]
        deck.listaAcciones.append(dataAccion.desdeDict({"nombre": "Macro", "key": 9, "accion": "macro", "opciones": pasos}))
        await user.open("/")
        user.find(marker="editar-deck-9").click()

        assert gui.formulario.editorAcción.value == "Macro"
        assert "teclas" in gui.formulario.opcionesEditar["Acciones"].value

        user.find(marker="editor-nombre").clear().type("Macro 2")
        user.find(marker="botonAgregar").click()
        await user.should_see("Macro 2 guardada en deck, tecla 9")

        macro = deck.listaAcciones[-1]
        assert (macro.nombre, macro.accion, macro.opciones) == ("Macro 2", "macro", pasos)

    async def test_editar_pasos_en_bloques(self, user: User, gui: miGui, deck: dispositivoFalso):
        pasos = [
            {"accion": "teclas", "opciones": {"teclas": ["s"]}},
            {"accion": "obs_escena", "opciones": {"escena": "Juego"}, "macro_opciones": {"respuesta": "x"}},
            {"accion": "delay", "opciones": {"tiempo": 1}},
        ]
        deck.listaAcciones.append(dataAccion.desdeDict({"nombre": "Macro", "key": 9, "accion": "macro", "opciones": pasos}))
        await user.open("/")
        user.find(marker="editar-deck-9").click()
        user.find(marker="botonEditarPasos").click()
        await user.should_see(marker="paso-2")

        user.find(marker="bajarPaso-0").click()
        user.find(marker="borrarPaso-2").click()
        # Paso sin clase OOP: opciones en YAML y conserva macro_opciones
        user.find(marker="editarPaso-0").click()
        user.find(marker="opción-paso-Opciones").clear().type("escena: Charla")
        user.find(marker="botonGuardarPaso").click()
        user.find(marker="botonAgregarPaso").click()
        user.find(marker="editorAcciónPaso").click()
        user.find("Delay").click()
        user.find(marker="opción-paso-Tiempo").type("2")
        user.find(marker="botonGuardarPaso").click()
        user.find(marker="botonListoPasos").click()

        user.find(marker="botonAgregar").click()
        await user.should_see("Macro guardada en deck, tecla 9")
        assert deck.listaAcciones[-1].opciones == [
            {"accion": "obs_escena", "opciones": {"escena": "Charla"}, "macro_opciones": {"respuesta": "x"}},
            {"accion": "teclas", "opciones": {"teclas": ["s"]}},
            {"accion": "delay", "opciones": {"tiempo": "2"}},
        ]



class TestPropiedadesFolder:
    async def test_crear_editar_y_quitar(self, user: User, guiPedal: miGui, pedal: MiPedal):
        await user.open("/")
        user.find(marker="propiedadesFolder-pedal").click()
        guiPedal.pestañas.propiedadesFolder.fondo.value = "#0606bb"
        guiPedal.pestañas.propiedadesFolder.tamaño.value = 40
        user.find(marker="botonGuardarFolder").click()

        assert pedal.propiedadFolder.aDict() == {
            "key": "propiedad_folder",
            "imagen_opciones": {"fondo": "#0606bb"},
            "titulo_opciones": {"tamanno_maximo": 40},
        }

        user.find(marker="propiedadesFolder-pedal").click()
        assert guiPedal.pestañas.propiedadesFolder.fondo.value == "#0606bb"
        guiPedal.pestañas.propiedadesFolder.fondo.value = ""
        guiPedal.pestañas.propiedadesFolder.tamaño.value = None
        user.find(marker="botonGuardarFolder").click()

        assert pedal.propiedadFolder is None, "vacía se quita del .md"

    async def test_fondo_del_folder_en_la_cuadricula(self, user: User, guiPedal: miGui, pedal: MiPedal):
        pedal.listaAcciones.append(dataAccion(key="propiedad_folder", imagenOpciones={"fondo": "#00ff00"}))
        await user.open("/")
        boton = next(iter(user.find(marker="tecla-pedal-1").elements))
        imagen = next(e for e in boton.descendants() if isinstance(e, ui.image)).source
        assert imagenVista(imagen).convert("RGB").getpixel((70, 70)) == (0, 255, 0)



class TestCuadriculaFolder:
    """Dispositivos sin botones físicos (MQTT, GUI) se dibujan con la cuadrícula de la propiedad_folder"""

    async def test_sin_cuadricula_es_lista(self, user: User, gui: miGui, deck: dispositivoFalso):
        assert deck.gruposBotones() is None
        await user.open("/")
        await user.should_see(marker="editar-deck-1")
        await user.should_not_see(marker="vista-lista-deck")

    async def test_teclas_numero_en_celdas_y_texto_aparte(self, user: User, gui: miGui, deck: dispositivoFalso):
        deck.listaAcciones.append(dataAccion(key="propiedad_folder", extra={"cuadricula": {"columnas": 3, "filas": 2}}))
        deck.listaAcciones.append(dataAccion(nombre="Luz", key="luz_on", accion="delay"))
        assert deck.cuadriculaFolder() == (3, 2)
        await user.open("/")
        await user.should_see(marker="tecla-deck-1")
        await user.should_see(marker="tecla-deck-6")
        await user.should_see("Otras teclas")
        await user.should_see(marker="tecla-deck-luz_on")

    async def test_valores_invalidos_no_dibujan(self, deck: dispositivoFalso):
        deck.listaAcciones.append(dataAccion(key="propiedad_folder", extra={"cuadricula": {"columnas": 0, "filas": "x"}}))
        assert deck.gruposBotones() is None

    async def test_guardar_desde_el_dialogo(self, user: User, gui: miGui, deck: dispositivoFalso):
        await user.open("/")
        user.find(marker="propiedadesFolder-deck").click()
        assert gui.pestañas.propiedadesFolder.filaCuadricula.visible
        gui.pestañas.propiedadesFolder.columnas.value = 4
        gui.pestañas.propiedadesFolder.filas.value = 2
        user.find(marker="botonGuardarFolder").click()
        assert deck.propiedadFolder.aDict() == {"key": "propiedad_folder", "cuadricula": {"columnas": 4, "filas": 2}}
        await user.should_see(marker="tecla-deck-8")

        user.find(marker="propiedadesFolder-deck").click()
        gui.pestañas.propiedadesFolder.columnas.value = None
        user.find(marker="botonGuardarFolder").click()
        assert deck.propiedadFolder is None, "sin columnas o filas se quita la cuadrícula"

    async def test_aparatos_fisicos_no_muestran_columnas(self, user: User, guiPedal: miGui):
        await user.open("/")
        user.find(marker="propiedadesFolder-pedal").click()
        assert not guiPedal.pestañas.propiedadesFolder.filaCuadricula.visible

    async def test_cambiar_vista_con_iconos(self, user: User, gui: miGui, deck: dispositivoFalso):
        deck.listaAcciones.append(dataAccion(key="propiedad_folder", extra={"cuadricula": {"columnas": 2, "filas": 1}}))
        await user.open("/")
        await user.should_see(marker="tecla-deck-1")
        user.find(marker="vista-lista-deck").click()
        await user.should_see(marker="editar-deck-1")
        await user.should_not_see(marker="intercambiar-deck")
        user.find(marker="vista-cuadricula-deck").click()
        await user.should_see(marker="intercambiar-deck")


class TestSubirFolder:
    async def test_sube_y_se_desactiva_en_la_raiz(self, user: User, monkeypatch, tmp_path):
        monkeypatch.setattr(sys.modules["elGarrobo.dispositivos.dispositivo"], "ObtenerFolderConfig", lambda: tmp_path)
        (tmp_path / "default" / "sub").mkdir(parents=True)
        (tmp_path / "default" / "pedal.json").write_text('[{"nombre": "Raiz", "key": 1}]')
        (tmp_path / "default" / "sub" / "pedal.json").write_text('[{"nombre": "Sub", "key": 1}]')
        pedal = MiPedal({"nombre": "pedal", "archivo": "pedal"})
        pedal.asignarPerfil("default")
        pedal.cargarAccionesFolder("/")
        pedal.cargarAccionesFolder("sub")
        gui = miGui({"nombre": "gui"})
        gui.listaClasesAcciones = cargarClasesAcciones()
        gui.listaDispositivos = [pedal]

        await user.open("/")
        assert next(iter(user.find(marker="subirFolder-pedal").elements)).enabled
        user.find(marker="subirFolder-pedal").click()

        await user.should_see("1: Raiz")
        assert pedal.enFolderRaiz()
        assert not next(iter(user.find(marker="subirFolder-pedal").elements)).enabled


class TestCrearFolder:
    @pytest.fixture
    def pedalEnPerfil(self, monkeypatch, tmp_path) -> MiPedal:
        monkeypatch.setattr(sys.modules["elGarrobo.dispositivos.dispositivo"], "ObtenerFolderConfig", lambda: tmp_path)
        (tmp_path / "default" / "existe").mkdir(parents=True)
        (tmp_path / "default" / "existe" / "pedal.md").write_text("--- []\n...\n")
        (tmp_path / "default" / "pedal.json").write_text(
            '[{"nombre": "Nuevo", "key": 1, "accion": "entrar_folder", "opciones": {"folder": "nuevo"}},'
            ' {"nombre": "Existe", "key": 2, "accion": "entrar_folder", "opciones": {"folder": "existe"}}]'
        )
        pedal = MiPedal({"nombre": "pedal", "archivo": "pedal"})
        pedal.asignarPerfil("default")
        pedal.cargarAccionesFolder("/")
        return pedal

    def test_dispositivo(self, pedalEnPerfil: MiPedal, tmp_path):
        assert pedalEnPerfil.tieneFolder("existe") and pedalEnPerfil.tieneFolder("/existe")
        assert not pedalEnPerfil.tieneFolder("nuevo")
        assert pedalEnPerfil.rutaFolder("../../fuera") is None and pedalEnPerfil.tieneFolder("../../fuera"), "fuera del perfil no se ofrece crear"

        pedalEnPerfil.cargarAccionesFolder("existe")
        assert str(pedalEnPerfil.folderActual) == "existe", "entra aunque el folder esté vacío"

    async def test_ejecutar_ofrece_crear(self, user: User, pedalEnPerfil: MiPedal, tmp_path):
        gui = miGui({"nombre": "gui"})
        gui.listaClasesAcciones = cargarClasesAcciones()
        gui.listaDispositivos = [pedalEnPerfil]
        gui.ejecutarAcción = MagicMock()
        await user.open("/")

        user.find(marker="tecla-pedal-2").click()
        user.find(marker="botonEjecutar").click()
        assert not gui.formulario.dialogoCrearFolder.value, "el folder existe, no pregunta"

        user.find(marker="tecla-pedal-1").click()
        user.find(marker="botonEjecutar").click()
        assert gui.formulario.dialogoCrearFolder.value
        await user.should_see("pedal no tiene acciones en nuevo")
        user.find(marker="botonCrearFolder").click()

        assert (tmp_path / "default" / "nuevo" / "pedal.md").exists()
        assert str(pedalEnPerfil.folderActual) == "nuevo" and pedalEnPerfil.listaAcciones == []

    async def test_guardar_ofrece_crear(self, user: User, pedalEnPerfil: MiPedal, tmp_path):
        gui = miGui({"nombre": "gui"})
        gui.listaClasesAcciones = cargarClasesAcciones()
        gui.listaDispositivos = [pedalEnPerfil]
        await user.open("/")

        user.find(marker="tecla-pedal-1").click()
        user.find(marker="botonAgregar").click()
        assert gui.formulario.dialogoCrearFolder.value


class TestAgregarTeclado:
    """Agregar y quitar teclados desde /dispositivos sin reiniciar"""

    @pytest.fixture
    def archivos(self, monkeypatch) -> dict:
        archivos = {"teclados.md": [{"nombre": "Completo", "dispositivo": "/dev/a", "archivo": "drevo"}]}
        monkeypatch.setattr(configuracion, "leerData", lambda _: {"teclado": True})
        monkeypatch.setattr(configuracion, "ObtenerArchivo", lambda archivo: archivos.get(archivo))
        monkeypatch.setattr(configuracion, "SalvarArchivo", lambda archivo, data: archivos.update({archivo: data}))
        return archivos

    @pytest.fixture(autouse=True)
    def tecladosConectados(self, monkeypatch) -> None:
        from elGarrobo.dispositivos.migui import agregar

        async def escucharFalso(ruta, alPresionar):
            if ruta == "/dev/b":
                alPresionar(ruta, "KEY_A")  # el usuario presiona una tecla en el Moonlander

        monkeypatch.setattr(MiTecladoMacro, "listarDisponibles", staticmethod(lambda: [("/dev/a", "DREVO"), ("/dev/b", "Moonlander")]))
        monkeypatch.setattr(agregar, "escucharTeclado", escucharFalso)

    async def test_agregar_elige_el_teclado_presionado(self, user: User, gui: miGui, archivos: dict):
        nuevo = MagicMock()
        nuevo.tieneFolder.return_value = False
        gui.agregarDispositivo = MagicMock(return_value=nuevo)
        await user.open("/dispositivos")

        user.find(marker="agregar-teclado").click()
        await user.should_see("Ya agregado")
        await user.should_see("KEY_A")
        user.find(marker="agregar-siguiente").click()
        # Paso 2: se escucha solo el elegido y su tecla se ilumina en las miniaturas
        tecla = next(iter(user.find(marker="mini-ingles_87k-KEY_A").elements))
        await esperarQue(lambda: f"bg-{tema.colorActivo}" in tecla.classes)
        user.find(marker="agregar-distribucion-ingles_87k").click()
        user.find(marker="agregar-nombre").type("completo")
        user.find(marker="agregar-guardar").click()
        await user.should_see("Ya existe completo")
        gui.agregarDispositivo.assert_not_called()

        user.find(marker="agregar-nombre").clear().type("Moon Lander")
        user.find(marker="agregar-guardar").click()
        # Archivo por defecto teclado_<nombre>; pestaña al final (deck tiene ordenar 0)
        data = {"nombre": "Moon Lander", "dispositivo": "/dev/b", "archivo": "teclado_moon_lander", "distribucion": "ingles_87k", "ordenar": -1}
        assert archivos["teclados.md"][-1] == data
        gui.agregarDispositivo.assert_called_once_with(MiTecladoMacro, data)
        nuevo.crearFolder.assert_called_once_with("/")
        await user.should_see("Moon Lander agregado y conectado")
        await user.should_see(marker="quitar-Moon Lander")

    async def test_archivo_sin_carpetas(self, user: User, gui: miGui, archivos: dict):
        gui.agregarDispositivo = MagicMock()
        await user.open("/dispositivos")
        user.find(marker="agregar-teclado").click()
        await user.should_see("KEY_A")
        user.find(marker="agregar-siguiente").click()
        user.find(marker="agregar-nombre").type("Moon")
        user.find(marker="agregar-archivo").type("../fuera")
        user.find(marker="agregar-guardar").click()
        await user.should_see("Solo letras, números, - y _")
        assert next(iter(user.find(kind=ui.expansion, content="Avanzado").elements)).value, "abre Avanzado para ver el error"
        gui.agregarDispositivo.assert_not_called()

    async def test_quitar_desconecta_y_borra_entrada(self, user: User, gui: miGui, archivos: dict):
        gui.quitarDispositivo = MagicMock()
        await user.open("/dispositivos")

        user.find(marker="quitar-Completo").click()
        clickEnDialogoAbierto(user, "Quitar")
        assert archivos["teclados.md"] == []
        gui.quitarDispositivo.assert_called_once_with("Completo")
        await user.should_see("Completo quitado, su archivo de acciones se conserva")
        await user.should_see("Conecta uno y presiona Agregar teclado")

    async def test_cambiar_distribucion_desde_dispositivos(self, user: User, gui: miGui, archivos: dict, monkeypatch):
        from elGarrobo.dispositivos.miteclado import mi_teclado_macro

        monkeypatch.setattr(mi_teclado_macro, "ObtenerArchivo", lambda archivo: archivos.get(archivo))
        monkeypatch.setattr(mi_teclado_macro, "SalvarArchivo", lambda archivo, data: archivos.update({archivo: data}))
        # Conectado con otro nombre (renombrado sin reiniciar): se encuentra por ruta
        conectado = MiTecladoMacro({"nombre": "Viejo", "dispositivo": "/dev/a"})
        gui.listaDispositivos.append(conectado)
        await user.open("/dispositivos")
        await user.should_see("Ninguna, sus teclas se ven como lista")

        user.find(marker="cambiarDistribucion-Completo").click()
        user.find(marker="opcionDistribucion-ingles_87k").click()
        assert archivos["teclados.md"][0]["distribucion"] == "ingles_87k"
        assert conectado.distribucion == "ingles_87k", "la pestaña de Acciones usa la nueva sin reiniciar"
        await user.should_not_see("Ninguna, sus teclas se ven como lista")

        user.find(kind=ui.button, content="Guardar").click()
        assert archivos["teclados.md"][0]["distribucion"] == "ingles_87k", "Guardar no regresa la anterior"

    async def test_estados_vacios_dicen_como_agregar(self, user: User, gui: miGui, archivos: dict, monkeypatch):
        monkeypatch.setattr(configuracion, "leerData", lambda _: {"teclado": False})
        await user.open("/dispositivos")
        await user.should_see("Aún no hay ningún Pedal StreamDeck")
        await user.should_see("Por ahora se agrega a mano en")
        await user.should_see("pedal.md")
        await user.should_not_see("No hay aparatos")
        # Tipo apagado: el motivo se lee, no queda en un tooltip del botón deshabilitado
        await user.should_see("Activa Teclado Macro para agregar uno")
        with user:
            next(s for s in user.find(kind=ui.switch).elements if s.props.get("aria-label") == "Activar Teclado Macro").value = True
        await user.should_not_see("Activa Teclado Macro para agregar uno")

    async def test_recargar_muestra_distribucion_nueva(self, user: User, gui: miGui, archivos: dict, distribucionesUsuario: Path):
        await user.open("/dispositivos")
        user.find(marker="agregar-teclado").click()
        await user.should_see("KEY_A")
        user.find(marker="agregar-siguiente").click()
        await user.should_see("¿No está tu teclado?")
        assert distribucionesUsuario.is_dir(), "la carpeta existe para que el usuario la encuentre"

        (distribucionesUsuario / "mia.json").write_text('[{"key": "KEY_A", "x": 0, "y": 0}]')
        user.find(marker="recargar-distribuciones").click()
        await user.should_see(marker="agregar-distribucion-mia")
        user.find(marker="agregar-distribucion-mia").click()
        user.find(marker="agregar-nombre").type("Moon")
        gui.agregarDispositivo = MagicMock()
        user.find(marker="agregar-guardar").click()
        assert archivos["teclados.md"][-1]["distribucion"] == "mia"

    async def test_siguiente_espera_elegir_teclado(self, user: User, gui: miGui, archivos: dict, monkeypatch):
        from elGarrobo.dispositivos.migui import agregar

        async def nadiePresiona(ruta, alPresionar):
            pass

        monkeypatch.setattr(agregar, "escucharTeclado", nadiePresiona)
        await user.open("/dispositivos")
        user.find(marker="agregar-teclado").click()
        await user.should_see("Moonlander")
        assert not next(iter(user.find(marker="agregar-siguiente").elements)).enabled
        user.find(marker="teclado-/dev/b").click()
        assert next(iter(user.find(marker="agregar-siguiente").elements)).enabled

    async def test_tipo_apagado_no_deja_agregar(self, user: User, gui: miGui, archivos: dict, monkeypatch):
        monkeypatch.setattr(configuracion, "leerData", lambda _: {"teclado": False})
        await user.open("/dispositivos")
        assert not next(iter(user.find(marker="agregar-teclado").elements)).enabled


class TestOrdenPestañas:
    async def test_bajar_guarda_y_mueve_las_pestañas(self, user: User, monkeypatch):
        archivos = {
            "teclados.md": [{"nombre": "A", "ordenar": 5}, {"nombre": "B", "ordenar": 3}, {"nombre": "Apagado"}],
            "pedal.md": [{"nombre": "P"}],
        }
        monkeypatch.setattr(configuracion, "leerData", lambda _: {})
        monkeypatch.setattr(configuracion, "ObtenerArchivo", lambda archivo: archivos.get(archivo))
        monkeypatch.setattr(configuracion, "SalvarArchivo", lambda archivo, data: archivos.update({archivo: data}))
        gui = miGui({"nombre": "gui"})
        a, b, p = MiTecladoMacro({"nombre": "A", "ordenar": 5}), MiTecladoMacro({"nombre": "B", "ordenar": 3}), MiPedal({"nombre": "P"})
        gui.listaDispositivos = [p, b, a]
        await user.open("/")
        user.find(marker="ordenarPestañas-A").click()
        await user.should_see("La primera de la lista va a la izquierda. Se guarda al mover")

        assert not next(iter(user.find(marker="subir-A").elements)).enabled, "la primera no sube"
        assert not next(iter(user.find(marker="bajar-P").elements)).enabled, "la última no baja"
        user.find(marker="bajar-A").click()

        assert [d.nombre for d in sorted(gui.listaDispositivos, key=lambda d: d.nivelOrdenar, reverse=True)] == ["B", "A", "P"]
        assert archivos["teclados.md"] == [{"nombre": "A", "ordenar": 2}, {"nombre": "B", "ordenar": 3}, {"nombre": "Apagado"}]
        assert archivos["pedal.md"] == [{"nombre": "P", "ordenar": 1}]
        assert [t.props["name"] for t in gui.pestañas.tabs.default_slot.children] == ["B", "A", "P"], "se mueven sin recargar"
        await user.should_see("A: posición 2 de 3")
        await esperarQue(lambda: not next(iter(user.find(marker="subir-B").elements)).enabled)  # redibujada con B primero

    async def test_con_un_solo_dispositivo_no_hay_orden(self, user: User, gui: miGui):
        await user.open("/")
        await user.should_not_see(marker="ordenarPestañas-deck")

    async def test_dispositivos_ya_no_tiene_orden(self, user: User, gui: miGui, monkeypatch):
        monkeypatch.setattr(configuracion, "leerData", lambda _: {})
        await user.open("/dispositivos")
        await user.should_not_see("Ordenar pestañas")
