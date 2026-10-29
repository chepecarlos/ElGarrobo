"""Página /eventos: acciones que se ejecutan cuando un módulo emite un evento (ej. una impresora termina)

Se guardan en eventos.md global; ElGarrobo lo lee en cada evento, así los cambios aplican sin reiniciar
"""

from nicegui import ui

from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.dialogos import dialogoPregunta
from elGarrobo.dispositivos.migui.editores import (
    avisarError,
    cargarOpciones,
    crearEditor,
    encabezado,
    leerOpciones,
    nombrar,
    ponerValor,
)
from elGarrobo.dispositivos.migui.pasos import editorPasos
from elGarrobo.miLibrerias import SalvarArchivo, leerData

CLAVES_FORMULARIO = ("nombre", "evento", "filtro", "accion", "opciones")
"Claves de una entrada que arma el formulario; las demás (activo, macro_opciones...) se conservan al guardar"


def catalogoEventos() -> dict:
    """Nombre del evento → (clase del módulo que lo emite, eventoModulo)"""
    # Al usarse y no arriba, igual que /modulos en migui.py
    from elGarrobo.modulos import cargarModulos

    return {evento.nombre: (clase, evento) for clase in cargarModulos() for evento in clase.eventos}


def mostrarEventos(listaClasesAcciones: dict, ejecutarAcción) -> None:
    """Lista de eventos agrupada por módulo con activar, probar, editar y borrar, y el diálogo para editarlos

    Args:
        listaClasesAcciones (dict): comando → clase de la acción
        ejecutarAcción: ejecuta una acción como si se presionara su tecla (para Probar)
    """
    from elGarrobo.modulos.modulo import ARCHIVO_EVENTOS, reemplazarDatos

    entradas: list[dict] = leerData(ARCHIVO_EVENTOS) or []
    catalogo = catalogoEventos()
    modulosActivos = leerData("modulos") or {}
    nombresAcciones = {comando: clase().nombre for comando, clase in listaClasesAcciones.items()}
    comandos = {nombre: comando for comando, nombre in nombresAcciones.items()}
    pasos = editorPasos(listaClasesAcciones)
    pregunta = dialogoPregunta()
    editando: dict = {"posición": None, "filtro": {}, "opciones": {}}
    "posición en entradas (None si es nueva) y editores del filtro y de las opciones"

    def guardarArchivo() -> None:
        SalvarArchivo(ARCHIVO_EVENTOS, entradas)
        lista.refresh()

    def etiquetaEvento(nombre: str) -> str:
        clase, evento = catalogo[nombre]
        apagado = "" if modulosActivos.get(clase.modulo) else " (módulo apagado)"
        return f"{clase.nombre} · {evento.descripcion}{apagado}"

    with ui.dialog() as dialogo, ui.card().classes("w-full max-w-2xl"):
        titulo = encabezado(ui.label("").classes("text-lg"), 2)
        editorNombre = ui.input("Nombre (opcional)").classes("w-full").props("clearable").mark("evento-nombre")
        editorEvento = ui.select({nombre: etiquetaEvento(nombre) for nombre in catalogo}, label="* Evento", on_change=lambda: mostrarFiltro({}))
        editorEvento.classes("w-full").mark("evento-evento")
        variables = ui.label("").classes("text-caption").mark("evento-variables")
        with ui.expansion("Filtro (opcional)", icon="filter_alt").classes("w-full"):
            ui.label("Solo se ejecuta si el dato es igual al elegido; vacío acepta cualquiera").classes("text-caption")
            columnaFiltro = ui.column().classes("w-full")
        editorAcción = ui.select(sorted(comandos), with_input=True, label="* Acción", on_change=lambda: mostrarOpciones(None))
        editorAcción.classes("w-full").mark("evento-accion")
        columnaOpciones = ui.column().classes("w-full")
        with ui.row():
            ui.button("Cancelar", on_click=dialogo.close).props("flat")
            ui.button("Guardar", icon="save", color=tema.colorOscuro, on_click=lambda: guardar()).mark("evento-guardar")

    def mostrarFiltro(filtro: dict) -> None:
        """Un campo por dato del evento elegido y la ayuda con sus variables"""
        columnaFiltro.clear()
        editando["filtro"] = {}
        clase, evento = catalogo.get(editorEvento.value, (None, None))
        datos = evento.datos if evento else {}
        variables.text = ("Variables para las opciones: " + " ".join(f"{{{dato}}}" for dato in datos)) if datos else ""
        with columnaFiltro:
            for dato, ejemplo in datos.items():
                valor = str(filtro.get(dato, ""))
                # Lo que vio el módulo al correr y lo ya usado en otros eventos (ej. una impresora apagada)
                conocidos = {*clase.valoresDatos.get(dato, []), valor}
                conocidos |= {str(e["filtro"][dato]) for e in entradas if dato in (e.get("filtro") or {})}
                conocidos.discard("")
                if conocidos:
                    editor = ui.select(
                        sorted(conocidos), label=dato, value=valor or None, with_input=True, new_value_mode="add-unique", clearable=True
                    )
                    editor.props["hint"] = "Elige de la lista o escribe otro y presiona Enter"
                else:
                    editor = ui.input(dato, value=valor, placeholder=f"ej. {ejemplo}")
                editando["filtro"][dato] = editor.classes("w-full").mark(f"evento-filtro-{dato}")

    def mostrarOpciones(opciones: dict | list | None) -> None:
        """Editores de las opciones de la acción; las acciones sin clase OOP se editan en YAML (igual que los pasos)"""
        columnaOpciones.clear()
        comando = comandos.get(editorAcción.value) or editorAcción.value
        claseAcción = listaClasesAcciones.get(comando)
        with columnaOpciones:
            if claseAcción is None:
                if comando:
                    propiedad = propiedadAccion("Opciones", "opciones", tipo=[dict, list])
                    editando["opciones"] = {propiedad.nombre: crearEditor(propiedad, "evento-opción-Opciones")}
                    ponerValor(editando["opciones"][propiedad.nombre], opciones)
                return
            objetoAcción = claseAcción()
            ui.label(objetoAcción.descripcion).classes(f"w-full bg-{tema.colorTecla} p-2 text-white rounded-lg")
            editando["opciones"] = {}
            for propiedad in objetoAcción.listaPropiedades:
                editor = crearEditor(propiedad, f"evento-opción-{propiedad.nombre}")
                editando["opciones"][propiedad.nombre] = editor
                if propiedad.atributo == objetoAcción.atributoLista:
                    ui.button("Editar pasos", icon="view_list", color=tema.colorOscuro, on_click=lambda e=editor: pasos.abrir(e)).classes("w-full")
        if opciones:
            cargarOpciones(editando["opciones"], claseAcción, opciones)

    def abrir(posición: int | None) -> None:
        """Abre el diálogo con la entrada guardada en esa posición, o vacío (None) para una nueva"""
        editando["posición"] = posición
        entrada = entradas[posición] if posición is not None else {}
        titulo.text = "Editar evento" if posición is not None else "Nuevo evento"
        editorNombre.value = entrada.get("nombre", "")
        evento = entrada.get("evento")
        if evento and evento not in catalogo:
            # De un módulo que ya no existe: se deja elegir para no perderlo al guardar
            editorEvento.options[evento] = evento
            editorEvento.update()
        editorEvento.value = evento
        mostrarFiltro(entrada.get("filtro") or {})
        comando = entrada.get("accion")
        editorAcción.value = nombresAcciones.get(comando, comando)
        mostrarOpciones(entrada.get("opciones"))
        dialogo.open()

    def guardar() -> None:
        if not editorEvento.value:
            avisarError(editorEvento, "Falta elegir el evento")
            return
        comando = comandos.get(editorAcción.value) or editorAcción.value
        if not comando:
            avisarError(editorAcción, "Falta elegir la acción")
            return
        claseAcción = listaClasesAcciones.get(comando)
        try:
            opciones = leerOpciones(editando["opciones"], claseAcción)
        except ValueError:
            return
        if claseAcción is None and isinstance(opciones, dict):
            opciones = opciones.get("opciones")

        posición = editando["posición"]
        anterior = entradas[posición] if posición is not None else {}
        entrada = {"nombre": editorNombre.value} if editorNombre.value else {}
        entrada["evento"] = editorEvento.value
        filtro = {dato: editor.value for dato, editor in editando["filtro"].items() if editor.value}
        if filtro:
            entrada["filtro"] = filtro
        entrada |= {clave: valor for clave, valor in anterior.items() if clave not in CLAVES_FORMULARIO}
        entrada["accion"] = comando
        if opciones:
            entrada["opciones"] = opciones

        if posición is None:
            entradas.append(entrada)
        else:
            entradas[posición] = entrada
        dialogo.close()
        guardarArchivo()
        ui.notify("Evento guardado, ya está funcionando", type="positive")

    def cambiarActivo(posición: int, activo: bool) -> None:
        # Activo es lo normal: solo se escribe activo: false para no llenar el .md
        if activo:
            entradas[posición].pop("activo", None)
        else:
            entradas[posición]["activo"] = False
        guardarArchivo()

    def probar(posición: int) -> None:
        entrada = entradas[posición]
        evento = catalogo.get(entrada.get("evento"), (None, None))[1]
        ejecutarAcción(reemplazarDatos(entrada, evento.datos if evento else {}))
        ui.notify("Ejecutada con datos de ejemplo")

    def borrar(posición: int) -> None:
        entradas.pop(posición)
        guardarArchivo()

    def resumen(entrada: dict) -> str:
        filtro = ", ".join(f"{dato} = {valor}" for dato, valor in (entrada.get("filtro") or {}).items()) or "siempre"
        comando = entrada.get("accion")
        return f"{filtro} → {nombresAcciones.get(comando, comando)}"

    @ui.refreshable
    def lista() -> None:
        if not entradas:
            ui.label("Todavía no hay eventos, agrega uno con +").classes("text-body2 px-4").mark("eventos-vacio")
            return
        # Agrupados por módulo en el orden del archivo
        grupos: dict[str, list[int]] = {}
        for posición, entrada in enumerate(entradas):
            clase = catalogo.get(entrada.get("evento"), (None, None))[0]
            grupos.setdefault(clase.nombre if clase else "Módulo desconocido", []).append(posición)
        for nombreGrupo, posiciones in grupos.items():
            with ui.column().classes(f"w-full gap-1 border-b border-{tema.colorOscuro} pb-4"):
                clase = catalogo.get(entradas[posiciones[0]].get("evento"), (None, None))[0]
                with ui.row().classes("items-center gap-2"):
                    encabezado(ui.label(nombreGrupo).classes("text-subtitle1 font-bold"), 3)
                    if clase is None or not modulosActivos.get(clase.modulo):
                        ui.badge("Módulo apagado", color=tema.colorPendiente, text_color="black")
                for posición in posiciones:
                    entrada = entradas[posición]
                    evento = catalogo.get(entrada.get("evento"), (None, None))[1]
                    nombre = entrada.get("nombre") or (evento.descripcion if evento else entrada.get("evento"))
                    # En celular los botones bajan a otra línea: a lo ancho dejaban el nombre en "Aviso fin …"
                    with ui.row().classes("items-center w-full gap-x-2 gap-y-0 sm:flex-nowrap").mark(f"evento-{posición}"):
                        interruptor = ui.switch(value=entrada.get("activo") is not False, on_change=lambda e, p=posición: cambiarActivo(p, e.value))
                        interruptor.props["aria-label"] = f"Activar {nombre}"
                        interruptor.mark(f"evento-activo-{posición}")
                        with ui.column().classes("gap-0 grow min-w-0 max-sm:basis-[calc(100%-5rem)]"):
                            ui.label(nombre).classes("font-bold truncate w-full")
                            ui.label(resumen(entrada)).classes("text-caption truncate w-full")
                        with ui.button_group().props("flat").classes("ml-auto"):
                            nombrar(ui.button(icon="play_arrow", on_click=lambda p=posición: probar(p)).props("flat").mark(f"evento-probar-{posición}"), "Probar con datos de ejemplo")
                            nombrar(ui.button(icon="edit", on_click=lambda p=posición: abrir(p)).props("flat").mark(f"evento-editar-{posición}"), "Editar")
                            nombrar(
                                ui.button(
                                    icon="delete",
                                    color=tema.colorPeligro,
                                    on_click=lambda p=posición, n=nombre: pregunta.preguntar(f"¿Borrar '{n}'?", "Borrar", lambda: borrar(p)),
                                ).props("flat").mark(f"evento-borrar-{posición}"),
                                "Borrar",
                            )

    with ui.column().classes("w-full max-w-3xl mx-auto gap-0"):
        with ui.row().classes("items-center justify-between w-full p-4"):
            encabezado(ui.label("Eventos").classes("text-h5"), 2)
            nombrar(ui.button(icon="add", color=tema.colorOscuro, on_click=lambda: abrir(None)).props("rounded").mark("evento-agregar"), "Agregar evento")
        ui.label("Acciones que se ejecutan cuando un módulo avisa algo, ej. una impresora termina. Los cambios aplican al momento.").classes("text-body2 px-4")
        with ui.column().classes("p-4 gap-4 w-full"):
            lista()
