"""Diálogo para editar los pasos de una macro como bloques en vez de YAML"""

import copy

import yaml
from nicegui import ui

from elGarrobo.accionesOOP import accion
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.catalogo import catalogoAcciones
from elGarrobo.dispositivos.migui.editores import (
    avisarError,
    cargarOpciones,
    crearEditor,
    encabezado,
    leerOpciones,
    leerValor,
    nombrar,
    ponerValor,
)


class editorPasos:
    """Abre los pasos del editor YAML de una macro como bloques (agregar, editar, borrar, subir/bajar) y al terminar
    los devuelve al editor YAML; se guardan en el .md con el resto del formulario
    """

    def __init__(self, listaClasesAcciones: dict[str, type[accion]]) -> None:
        self.listaClasesAcciones = listaClasesAcciones
        "comando → clase de la acción"
        self.listaNombres: list[str] = []
        "Nombres que muestra el selector de acción"
        self.comandos: dict[str, str] = {}
        "nombre → comando de la acción"
        for claseAcción in listaClasesAcciones.values():
            objetoClase: accion = claseAcción()
            self.listaNombres.append(objetoClase.nombre)
            self.comandos.setdefault(objetoClase.nombre, objetoClase.comando)
        self.pasos: list[dict] = []
        self.editando: int | None = None
        "Índice del paso en el formulario, None si es uno nuevo"
        self.editorYAML: ui.element = None
        "Editor YAML de la macro que se llena al terminar"
        self.editorAcción: ui.select = None
        self.propiedades: ui.column = None
        self.opciones: dict[str, ui.element] = {}
        self.catalogo = catalogoAcciones(listaClasesAcciones)
        "Panel para buscar acciones, lo reusan el formulario y /eventos"

        with ui.dialog() as self.dialogo, ui.card().classes("w-full max-w-2xl"):
            encabezado(ui.label("Pasos de la macro").classes("text-lg"), 2)
            self.lista = ui.column().classes("w-full gap-1")
            self.formulario = ui.column().classes("w-full")
            with ui.row():
                ui.button("Agregar paso", icon="add", color=tema.colorOscuro, on_click=lambda: self.editar(None)).mark("botonAgregarPaso")
                ui.button("Cancelar", on_click=self.dialogo.close).props("flat")
                ui.button("Listo", icon="check", color=tema.colorOscuro, on_click=self.terminar).mark("botonListoPasos")

    def abrir(self, editor: ui.element) -> None:
        """Abre los pasos del editor YAML de la macro como bloques"""
        try:
            pasos = leerValor(editor) or []
        except ValueError as error:
            avisarError(editor, str(error))
            return
        self.editorYAML = editor
        self.pasos = copy.deepcopy(pasos)
        self.cerrarPaso()
        self.dibujar()
        self.dialogo.open()

    def terminar(self) -> None:
        """Devuelve los pasos al editor YAML; se guardan en el .md con el resto del formulario"""
        ponerValor(self.editorYAML, self.pasos)
        self.dialogo.close()

    def dibujar(self) -> None:
        """Un bloque por paso con su acción, un resumen de sus opciones y botones para ordenar, editar y borrar"""
        self.lista.clear()
        with self.lista:
            if not self.pasos:
                ui.label("Sin pasos, agrega uno").classes("text-xs")
            for i, paso in enumerate(self.pasos):
                comando = paso.get("accion")
                claseAcción = self.listaClasesAcciones.get(comando)
                opciones = paso.get("opciones")
                resumen = yaml.safe_dump(opciones, allow_unicode=True, default_flow_style=True, width=1000).strip() if opciones else ""
                with ui.card().classes("w-full p-2").mark(f"paso-{i}"):
                    with ui.row().classes("w-full items-center no-wrap gap-2"):
                        ui.label(f"{i + 1}.").classes("font-bold")
                        with ui.column().classes("gap-0 grow min-w-0"):
                            ui.label(claseAcción().nombre if claseAcción else comando)
                            ui.label(resumen).classes("text-xs truncate w-full").tooltip(resumen)
                        with ui.button_group().props("flat"):
                            nombrar(ui.button(icon="arrow_upward", on_click=lambda i=i: self.mover(i, -1)).props(f"flat {'disable' if i == 0 else ''}").mark(f"subirPaso-{i}"), "Subir paso")
                            nombrar(ui.button(icon="arrow_downward", on_click=lambda i=i: self.mover(i, 1)).props(f"flat {'disable' if i == len(self.pasos) - 1 else ''}").mark(f"bajarPaso-{i}"), "Bajar paso")
                            nombrar(ui.button(icon="edit", on_click=lambda i=i: self.editar(i)).props("flat").mark(f"editarPaso-{i}"), "Editar paso")
                            nombrar(ui.button(icon="delete", color=tema.colorPeligro, on_click=lambda i=i: self.borrar(i)).props("flat").mark(f"borrarPaso-{i}"), "Borrar paso")

    def mover(self, i: int, cambio: int) -> None:
        self.pasos[i], self.pasos[i + cambio] = self.pasos[i + cambio], self.pasos[i]
        self.cerrarPaso()
        self.dibujar()

    def borrar(self, i: int) -> None:
        self.pasos.pop(i)
        self.cerrarPaso()
        self.dibujar()

    def cerrarPaso(self) -> None:
        self.formulario.clear()
        self.editando = None

    def editar(self, i: int | None) -> None:
        """Formulario de un paso (None para uno nuevo): acción y sus opciones con los mismos editores del formulario"""
        self.cerrarPaso()
        self.editando = i
        paso = self.pasos[i] if i is not None else {}
        comando = paso.get("accion")
        claseAcción = self.listaClasesAcciones.get(comando)
        nombres = self.listaNombres + ([comando] if comando and claseAcción is None else [])
        with self.formulario:
            ui.separator()
            ui.label(f"Paso {i + 1}" if i is not None else "Paso nuevo").classes("font-bold")
            # add-unique: se puede escribir el comando de una acción sin clase OOP (ej. obs_escena)
            self.editorAcción = (
                ui.select(nombres, with_input=True, new_value_mode="add-unique", label="Acción", value=claseAcción().nombre if claseAcción else comando, on_change=lambda: self.mostrarOpciones(None))
                .classes("w-full")
                .mark("editorAcciónPaso")
            )
            self.catalogo.agregarBoton(self.editorAcción)
            self.propiedades = ui.column().classes("w-full")
            with ui.row():
                ui.button("Guardar paso", icon="check", color=tema.colorOscuro, on_click=self.guardar).mark("botonGuardarPaso")
                ui.button("Cancelar", on_click=self.cerrarPaso).props("flat")
        self.mostrarOpciones(paso.get("opciones"))

    def comando(self) -> str | None:
        valor = self.editorAcción.value
        return self.comandos.get(valor) or valor

    def mostrarOpciones(self, opciones: dict | list | None) -> None:
        """Editores de las opciones del paso; las acciones sin clase OOP se editan en YAML"""
        claseAcción = self.listaClasesAcciones.get(self.comando())
        self.propiedades.clear()
        with self.propiedades:
            if claseAcción is None:
                propiedad = propiedadAccion("Opciones", "opciones", tipo=[dict, list])
                self.opciones = {propiedad.nombre: crearEditor(propiedad, "opción-paso-Opciones")}
                ponerValor(self.opciones[propiedad.nombre], opciones)
                return
            self.opciones = {propiedad.nombre: crearEditor(propiedad, f"opción-paso-{propiedad.nombre}") for propiedad in claseAcción().listaPropiedades}
        if opciones:
            cargarOpciones(self.opciones, claseAcción, opciones)

    def guardar(self) -> None:
        comando = self.comando()
        if not comando:
            avisarError(self.editorAcción, "Falta elegir la acción")
            return
        claseAcción = self.listaClasesAcciones.get(comando)
        try:
            opciones = leerOpciones(self.opciones, claseAcción)
        except ValueError:
            return
        if claseAcción is None and isinstance(opciones, dict):
            # Sin clase OOP: el único editor es el YAML de mostrarOpciones
            opciones = opciones.get("opciones")
        # Se copian las claves extra del paso (ej. macro_opciones)
        paso = dict(self.pasos[self.editando]) if self.editando is not None else {}
        paso["accion"] = comando
        paso.pop("opciones", None)
        if opciones:
            paso["opciones"] = opciones
        if self.editando is None:
            self.pasos.append(paso)
        else:
            self.pasos[self.editando] = paso
        self.cerrarPaso()
        self.dibujar()
