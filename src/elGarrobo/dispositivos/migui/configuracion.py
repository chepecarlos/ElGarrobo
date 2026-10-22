"""Páginas de configuración de la GUI: /modulos, /dispositivos y /configurar

Funciones sin estado: cada página arma sus widgets al abrirse, así cada pestaña del navegador tiene los suyos
"""

from nicegui import ui

from elGarrobo import servicio
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.agregar import dialogoAgregarTeclado
from elGarrobo.dispositivos.migui.dialogos import dialogoPregunta
from elGarrobo.dispositivos.migui.editores import encabezado, marcarError
from elGarrobo.miLibrerias import ObtenerArchivo, SalvarArchivo, SalvarValor, leerData


def marcarPendiente(gui, clave: str, descripción: str | None) -> None:
    """Agrega un cambio que espera reinicio, o lo quita con descripción None; la cabecera muestra el botón Reiniciar

    Args:
        gui (miGui): guarda los pendientes de todas las páginas; sin ella no hace nada
        clave (str): identifica el cambio, el siguiente con la misma clave lo reemplaza
        descripción (str): lo que se ve en el tooltip del botón (ej. "Pedal StreamDeck activado")
    """
    if gui is None:
        return
    pendientes = {k: v for k, v in gui.pendientesReinicio.items() if k != clave}
    if descripción is not None:
        pendientes[clave] = descripción
    # Dict nuevo y no modificado: bind_*_from compara con el valor anterior y el mismo objeto no cuenta como cambio
    gui.pendientesReinicio = pendientes


def mostrarListaActivables(titulo: str, archivo: str, listaClases: list, aviso: str, gui=None) -> None:
    """Lista módulos o dispositivos con un switch para activarlos/desactivarlos

    Args:
        titulo (str): Título de la página
        archivo (str): Archivo de configuración ("modulos" o "dispositivos")
        listaClases (list): Clases con atributos `modulo`, `nombre` y `descripcion`
        aviso (str): qué se aplica al reiniciar y qué al momento, debajo del título
        gui (miGui): marca los cambios pendientes de reinicio y agrega o quita aparatos al momento; sin ella solo se editan
    """
    configuracion = leerData(archivo) or {}

    def cambiarEstado(clave: str, valor: bool, nombre: str) -> None:
        SalvarValor(archivo, clave, valor)
        alArrancar = gui.valoresAlArrancar.setdefault(f"{archivo}.{clave}", not valor) if gui else not valor
        if valor == alArrancar:
            marcarPendiente(gui, f"{archivo}.{clave}", None)
            ui.notify(f"{nombre} queda {'activado' if valor else 'apagado'} como estaba")
            return
        marcarPendiente(gui, f"{archivo}.{clave}", f"{nombre} {'activado' if valor else 'apagado'}")
        ui.notify(f"{nombre} se {'activará' if valor else 'apagará'} al reiniciar ElGarrobo")

    encabezado(ui.label(titulo).classes("text-h5 p-4"), 2)
    ui.label(aviso).classes("text-caption px-4")
    with ui.column().classes("p-4 gap-2 w-full"):
        for clase in listaClases:
            activo = configuracion.get(clase.modulo, False)
            # no-wrap: en celular una descripción larga bajaba el texto debajo del switch
            with ui.row().classes(f"items-center w-full no-wrap border-b border-{tema.colorOscuro} pb-2"):
                interruptor = ui.switch(value=activo, on_change=lambda e, c=clase: cambiarEstado(c.modulo, e.value, c.nombre))
                interruptor.props["aria-label"] = f"Activar {clase.nombre}"
                with ui.column().classes("gap-0 min-w-0"):
                    # Junto al nombre y no al final de la fila: en pantallas anchas quedaría lejos del switch
                    with ui.row().classes("items-center gap-x-2 gap-y-0"):
                        ui.label(clase.nombre).classes("font-bold")
                        if gui is not None:
                            pendiente = ui.badge("Pendiente de reinicio", color=tema.colorPendiente, text_color="black")
                            pendiente.mark(f"pendiente-{clase.modulo}")
                            clave = f"{archivo}.{clase.modulo}"
                            pendiente.bind_visibility_from(gui, "pendientesReinicio", backward=lambda p, c=clave: c in p)
                    ui.label(clase.descripcion).classes("text-caption")
            # En dispositivos archivoConfiguracion es una lista de aparatos, en módulos un dict de opciones
            if issubclass(clase, dispositivo) and clase.archivoConfiguracion:
                mostrarAparatos(clase, gui, interruptor)
            elif getattr(clase, "propiedades", None):
                mostrarConfiguracionModulo(clase, gui)


def guardarOrden(dispositivos: list[dispositivo]) -> None:
    """La primera pestaña recibe el ordenar más alto; se guarda en el archivo de cada tipo (teclados.md, pedal.md…)"""
    for nivel, dispositivoActual in zip(range(len(dispositivos), 0, -1), dispositivos):
        dispositivoActual.nivelOrdenar = nivel
    for archivo in {type(d).archivoConfiguracion for d in dispositivos} - {""}:
        aparatos = ObtenerArchivo(archivo)
        if not isinstance(aparatos, list):
            continue
        niveles = {d.nombre: d.nivelOrdenar for d in dispositivos if type(d).archivoConfiguracion == archivo}
        for data in aparatos:
            if data.get("nombre") in niveles:
                data["ordenar"] = niveles[data["nombre"]]
        SalvarArchivo(archivo, aparatos)


def dialogoOrdenPestañas(dispositivos: list[dispositivo], alMover) -> callable:
    """Diálogo con los dispositivos en el orden de sus pestañas y botones para subir y bajar; se guarda al mover

    Args:
        dispositivos (list): dispositivos de las pestañas, se muestran por nivelOrdenar
        alMover: se llama después de guardar, para mover las pestañas al nuevo orden
    Returns:
        callable: abre el diálogo con el orden actual
    """
    foco: dict = {}
    "Dispositivo y dirección del último botón presionado: el refresh lo recrea y hay que devolverle el foco"

    @ui.refreshable
    def lista() -> None:
        orden = sorted(dispositivos, key=lambda d: d.nivelOrdenar, reverse=True)

        def mover(desde: int, hacia: int, marca: str) -> None:
            orden[desde], orden[hacia] = orden[hacia], orden[desde]
            guardarOrden(orden)
            foco.update(nombre=orden[hacia].nombre, marca=marca)
            estado.text = f"{orden[hacia].nombre}: posición {hacia + 1} de {len(orden)}"
            alMover()
            lista.refresh()

        for posición, dispositivoActual in enumerate(orden):
            nombre = dispositivoActual.nombre
            activos: dict[str, ui.button] = {}
            with ui.row().classes(f"items-center w-full no-wrap border-b border-{tema.colorOscuro} py-1"):
                ui.icon(dispositivoActual.icono)
                ui.label(nombre).classes("font-bold grow truncate min-w-0").props(f'title="{nombre}"')
                ui.label(getattr(type(dispositivoActual), "nombre", dispositivoActual.tipo)).classes("text-caption truncate max-sm:hidden")
                for icono, texto, hacia, marca in (
                    ("arrow_upward", "Subir", posición - 1, "subir"),
                    ("arrow_downward", "Bajar", posición + 1, "bajar"),
                ):
                    boton = ui.button(icon=icono, on_click=lambda p=posición, h=hacia, m=marca: mover(p, h, m)).props("flat round dense")
                    boton.props["aria-label"] = f"{texto} {nombre}"
                    boton.mark(f"{marca}-{nombre}")
                    if 0 <= hacia < len(orden):
                        activos[marca] = boton
                    else:
                        # Invisible y no solo deshabilitada: apagada casi no se distingue, y así no cambia el ancho
                        boton.disable()
                        boton.classes("invisible")
            if foco.get("nombre") == nombre:
                # En la orilla su botón desaparece: el foco pasa al otro para seguir moviéndolo con el teclado
                objetivo = activos.get(foco["marca"]) or next(iter(activos.values()), None)
                if objetivo is not None:
                    ui.run_javascript(f"setTimeout(() => getHtmlElement({objetivo.id})?.focus(), 50)")

    with ui.dialog() as dialogo, ui.card().classes("w-full max-w-xl"):
        encabezado(ui.label("Ordenar pestañas").classes("text-h6"), 3)
        ui.label("La primera de la lista va a la izquierda. Se guarda al mover").classes("text-caption")
        lista()
        with ui.row().classes("items-center w-full no-wrap"):
            estado = ui.label("").classes("text-caption grow").mark("orden-estado")
            estado.props["aria-live"] = "polite"
            ui.button("Listo", on_click=dialogo.close).props("flat")

    def abrir() -> None:
        foco.clear()
        estado.text = ""
        lista.refresh()
        dialogo.open()

    return abrir


def mostrarConfigurar(nombreTema: str, cambiarTema) -> None:
    """Opciones generales de ElGarrobo: arranque automático al iniciar sesión y tema de la interfaz

    Args:
        nombreTema (str): tema actual, una clave de tema.TEMAS
        cambiarTema: recibe la clave del tema elegido; lo aplica y lo guarda
    """

    def cambiarAutoarranque(valor: bool) -> None:
        servicio.cambiarAutoarranque(valor)
        ui.notify("ElGarrobo iniciará al encender la PC" if valor else "ElGarrobo ya no iniciará al encender la PC")

    encabezado(ui.label("Configurar").classes("text-h5 p-4"), 2)
    with ui.column().classes("p-4 gap-2 w-full"):
        with ui.row().classes(f"items-center w-full border-b border-{tema.colorOscuro} pb-2"):
            interruptor = ui.switch(value=servicio.autoarranque().exists(), on_change=lambda e: cambiarAutoarranque(e.value))
            interruptor.props["aria-label"] = "Iniciar al encender la PC"
            interruptor.mark("autoarranque")
            with ui.column().classes("gap-0"):
                ui.label("Iniciar al encender la PC").classes("font-bold")
                ui.label("Abre el ícono de la barra de estado al iniciar sesión, y este arranca ElGarrobo").classes("text-caption")
        with ui.row().classes(f"items-center w-full border-b border-{tema.colorOscuro} pb-2"):
            selector = ui.toggle(tema.NOMBRES_TEMAS, value=nombreTema, on_change=lambda e: cambiarTema(e.value))
            selector.props("no-caps aria-label=Tema").mark("tema")
            with ui.column().classes("gap-0"):
                ui.label("Tema").classes("font-bold")
                ui.label("Automático sigue el tema claro u oscuro de la PC o el celular").classes("text-caption")


def mostrarConfiguracionModulo(clase: type, gui=None) -> None:
    """Desplegable para editar la configuración de un módulo (ej. modulos/estado_octoprint.md)

    El formulario sale de `clase.propiedades` y no del archivo: aparecen todas las opciones aunque el archivo
    no exista o le falten, con su valor por defecto. Las propiedades con `elementos` (ej. impresoras) se pueden
    agregar y quitar. Un campo vacío se quita del archivo para que el módulo use su valor por defecto, y las
    claves del archivo que no están en las propiedades se guardan igual.
    """
    archivo = clase.archivoConfiguracion
    data = ObtenerArchivo(archivo)
    data = data if isinstance(data, dict) else {}
    editores: list[tuple[propiedadAccion, ui.element]] = []
    recienAgregado: list[dict] = []
    "Elemento que se acaba de agregar, se muestra abierto"

    def campo(contenedor: dict, propiedad: propiedadAccion, marca: str) -> None:
        valor = contenedor.get(propiedad.atributo, propiedad.defecto)
        if bool in propiedad.tipo:
            editor = ui.switch(propiedad.nombre, value=bool(valor))
        elif int in propiedad.tipo or float in propiedad.tipo:
            valor = valor if isinstance(valor, (int, float)) else None
            editor = ui.number(propiedad.nombre, value=valor, precision=0 if int in propiedad.tipo else None)
        else:
            secreto = propiedad.atributo in ("token", "clave", "password")
            texto = "" if valor is None else str(valor)
            editor = ui.input(
                propiedad.nombre,
                value=texto,
                placeholder=propiedad.ejemplo,
                password=secreto,
                password_toggle_button=secreto,
            )
        if propiedad.descripcion:
            editor.tooltip(propiedad.descripcion)
        editor.mark(f"config-{marca}-{propiedad.atributo}")

        def actualizar(evento, contenedor=contenedor, propiedad=propiedad) -> None:
            # Se guarda al escribir para que agregar o quitar elementos (refresh) no pierda lo editado
            if evento.value in (None, ""):
                contenedor.pop(propiedad.atributo, None)
            else:
                contenedor[propiedad.atributo] = int(evento.value) if int in propiedad.tipo else evento.value

        editor.on_value_change(actualizar)
        editores.append((propiedad, editor))

    def campos(contenedor: dict, propiedades: list[propiedadAccion], marca: str) -> None:
        with ui.row().classes("items-start gap-4 p-2"):
            for propiedad in propiedades:
                if not propiedad.elementos:
                    campo(contenedor, propiedad, marca)
        for propiedad in propiedades:
            if propiedad.elementos:
                lista(contenedor, propiedad, marca)

    def lista(contenedor: dict, propiedad: propiedadAccion, marca: str) -> None:
        elementos = contenedor.setdefault(propiedad.atributo, [])

        def agregar() -> None:
            nuevo = {p.atributo: p.defecto for p in propiedad.elementos if p.defecto is not None}
            elementos.append(nuevo)
            recienAgregado[:] = [nuevo]
            formulario.refresh()

        def quitar(número: int) -> None:
            elementos.pop(número)
            formulario.refresh()

        ui.label(propiedad.nombre).classes("font-bold px-2")
        for número, elemento in enumerate(elementos):
            titulo = str(elemento.get("nombre") or f"{propiedad.nombre} {número + 1}")
            abierto = any(elemento is otro for otro in recienAgregado)
            with ui.expansion(titulo, icon="tune", value=abierto) as desplegable:
                desplegable.classes(f"w-full border border-{tema.colorOscuro} rounded")
                campos(elemento, propiedad.elementos, f"{marca}-{número}")
                botonQuitar = ui.button(
                    "Quitar", icon="delete", color="negative", on_click=lambda n=número: quitar(n)
                )
                botonQuitar.props("flat").classes("m-2").mark(f"quitar-{marca}-{número}")
        botonAgregar = ui.button("Agregar", icon="add", color=tema.colorOscuro, on_click=agregar)
        botonAgregar.props("flat").classes("m-2").mark(f"agregar-{marca}-{propiedad.atributo}")

    @ui.refreshable
    def formulario() -> None:
        editores.clear()
        campos(data, clase.propiedades, clase.modulo)

    def guardar() -> None:
        faltan = [editor for propiedad, editor in editores if propiedad.obligatorio and editor.value in (None, "")]
        for _, editor in editores:
            marcarError(editor, "Obligatorio" if editor in faltan else None)
        if faltan:
            ui.notify("Faltan valores obligatorios", type="warning")
            return
        SalvarArchivo(archivo, data)
        marcarPendiente(gui, archivo, f"opciones de {clase.nombre}")
        ui.notify(f"{clase.nombre} guardado; se aplica al reiniciar ElGarrobo", type="positive")

    with ui.column().classes("w-full pl-12 gap-1"):
        with ui.expansion("Configuración", caption=archivo, icon="settings") as desplegable:
            desplegable.classes(f"w-full border border-{tema.colorOscuro} rounded")
            formulario()
            guardarBoton = ui.button("Guardar", icon="save", color=tema.colorOscuro, on_click=guardar)
            guardarBoton.classes("m-2").mark(f"guardar-{clase.modulo}")




def mostrarAparatos(clase: type[dispositivo], gui=None, interruptor: ui.switch | None = None) -> None:
    """Lista los aparatos de un tipo (ej. teclados.md) con un desplegable para editar el nombre

    Las clases con listarDisponibles (teclados) además se pueden agregar y quitar sin reiniciar, si hay gui
    """
    archivo = clase.archivoConfiguracion
    agregable = gui is not None and hasattr(clase, "listarDisponibles")

    def guardar(data: dict, nombre: ui.input, internos: list, desplegable: ui.expansion) -> None:
        aparatos = ObtenerArchivo(archivo) or []
        nombreAnterior = data.get("nombre")
        nombreNuevo = (nombre.value or "").strip()
        error = None
        # elGarrobo busca dispositivos por nombre sin importar mayúsculas (ej. entrar_folder con 'dispositivo')
        if any(otro.get("nombre") != nombreAnterior and str(otro.get("nombre")).lower() == nombreNuevo.lower() for otro in aparatos):
            error = f"Ya existe {nombreNuevo}"
        marcarError(nombre, "El nombre no puede quedar vacío" if not nombreNuevo else error)
        vacíos = [editor for _, editor in internos if not (editor.value or "").strip()]
        for _, editor in internos:
            marcarError(editor, "Falta el nombre" if editor in vacíos else None)
        if not nombreNuevo or error or vacíos:
            return
        data["nombre"] = nombreNuevo
        for dataInterno, editor in internos:
            dataInterno["nombre"] = editor.value.strip()
        # Se reemplaza su entrada en el archivo leído ahora, por si se agregó o quitó otro aparato desde que se dibujó
        SalvarArchivo(archivo, [data if otro.get("nombre") == nombreAnterior else otro for otro in aparatos])
        desplegable.text = nombreNuevo
        marcarPendiente(gui, f"{archivo}:{data.get('dispositivo', nombreAnterior)}", f"{nombreNuevo} editado")
        ui.notify(f"{nombreNuevo} guardado; se aplica al reiniciar ElGarrobo", type="positive")

    def agregar(data: dict) -> None:
        # Pestaña al final: se ordenan de mayor a menor ordenar
        data["ordenar"] = min((d.nivelOrdenar for d in gui.listaDispositivos), default=1) - 1
        SalvarArchivo(archivo, (ObtenerArchivo(archivo) or []) + [data])
        nuevo = gui.agregarDispositivo(clase, data)
        if not nuevo.tieneFolder("/"):
            nuevo.crearFolder("/")
        ui.notify(f"{data['nombre']} agregado y conectado", type="positive")
        lista.refresh()

    def quitar(nombre: str) -> None:
        SalvarArchivo(archivo, [data for data in ObtenerArchivo(archivo) or [] if data.get("nombre") != nombre])
        gui.quitarDispositivo(nombre)
        ui.notify(f"{nombre} quitado, su archivo de acciones se conserva")
        lista.refresh()

    def abrirAgregar() -> None:
        aparatos = ObtenerArchivo(archivo) or []
        nombres = {str(d.nombre).lower() for d in gui.listaDispositivos} | {str(a.get("nombre")).lower() for a in aparatos}
        dialogoAgregar.abrir({a.get("dispositivo") for a in aparatos}, nombres)

    @ui.refreshable
    def lista() -> None:
        aparatos = ObtenerArchivo(archivo) or []
        if not aparatos:
            ui.label(f"No hay aparatos en {archivo}").classes("text-caption")
        for data in aparatos:
            titulo, ruta = data.get("nombre", "Sin nombre"), data.get("dispositivo", "")
            with ui.expansion(titulo, caption=clase.nombreAparato(ruta), icon=clase.icono) as desplegable:
                desplegable.classes(f"w-full border border-{tema.colorOscuro} rounded")
                nombre = ui.input("Nombre", value=data.get("nombre", "")).classes("p-2")
                # Aparatos dentro de otro, ej. los StreamDeck de deck_combinado.md (streamDecks / streamDecksPlus)
                internos = [
                    interno
                    for valor in data.values()
                    if isinstance(valor, list)
                    for interno in valor
                    if isinstance(interno, dict) and "nombre" in interno
                ]
                editoresInternos = []
                if internos:
                    ui.label("Aparatos internos").classes("text-caption px-2")
                    with ui.row().classes("items-start gap-4 px-2"):
                        for interno in internos:
                            etiqueta = f"Nombre · {interno.get('dispositivo', '')}"
                            editor = ui.input(etiqueta, value=interno["nombre"])
                            editoresInternos.append((interno, editor))
                with ui.row().classes("m-2"):
                    ui.button(
                        "Guardar",
                        icon="save",
                        color=tema.colorOscuro,
                        on_click=lambda d=data, n=nombre, i=editoresInternos, e=desplegable: guardar(d, n, i, e),
                    )
                    if agregable:
                        quitarBoton = ui.button(
                            "Quitar",
                            icon="delete",
                            color=tema.colorPeligro,
                            on_click=lambda t=titulo: pregunta.preguntar(
                                f"¿Quitar {t}? Se desconecta y su archivo de acciones se conserva", "Quitar", lambda: quitar(t)
                            ),
                        )
                        quitarBoton.props("flat").mark(f"quitar-{titulo}")

    if agregable:
        dialogoAgregar = dialogoAgregarTeclado(agregar)
        pregunta = dialogoPregunta()
    with ui.column().classes("w-full pl-12 gap-1"):
        lista()
        if agregable:
            boton = ui.button(f"Agregar {clase.tipo}", icon="add", color=tema.colorOscuro, on_click=abrirAgregar)
            boton.mark(f"agregar-{clase.modulo}")
            if interruptor is not None:
                # Con el tipo apagado ElGarrobo no carga sus aparatos: no tiene sentido conectar uno suelto
                boton.bind_enabled_from(interruptor, "value")
                boton.tooltip(f"Activa {clase.nombre} para agregar")
