"""Páginas de configuración de la GUI: /modulos, /dispositivos y /configurar

Funciones sin estado: cada página arma sus widgets al abrirse, así cada pestaña del navegador tiene los suyos
"""

from pathlib import Path

from nicegui import ui

from elGarrobo import servicio
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.agregar import dialogoAgregar
from elGarrobo.dispositivos.migui.dialogos import dialogoPregunta
from elGarrobo.dispositivos.migui.distribucion import dialogoDistribucion, miniatura
from elGarrobo.dispositivos.migui.editores import campoPropiedad, encabezado, marcarError
from elGarrobo.miLibrerias import ObtenerArchivo, ObtenerFolderConfig, SalvarArchivo, SalvarValor, leerData


CONTENIDO_TIPO = "w-full pl-[4.5rem] max-sm:pl-6"
"Aparatos y opciones bajo su tipo: 4.5rem es el ancho del switch, así empiezan donde el nombre del tipo"
DESPLEGABLE_LIGERO = 'expand-separator header-class="pl-0"'
"Aparato como fila y no como tarjeta con borde (pesaba más que el tipo); sin padding izquierdo se alinea con el nombre"


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


def estadoAparato(instancia: dispositivo | None, tipoActivo: bool) -> tuple[str, str]:
    """Texto y color del chip de un aparato en /dispositivos

    Args:
        instancia (dispositivo): el que ElGarrobo tiene cargado para ese aparato, None si no lo cargó
        tipoActivo (bool): switch de su tipo; sin instancia explica por qué no está cargado
    """
    if instancia is None:
        return ("Apagado", "grey-6") if not tipoActivo else ("Se carga al reiniciar", tema.colorPendiente)
    # Grupo de StreamDeck: conectado solo si están todos, si no cuántos
    decks = getattr(instancia, "listaDeck", None)
    if decks:
        conectados = sum(bool(d.conectado) for d in decks)
        if conectados < len(decks):
            return (f"{conectados} de {len(decks)} conectados", "negative" if not conectados else tema.colorPendiente)
        return "Conectado", "positive"
    return ("Conectado", "positive") if instancia.conectado else ("Desconectado", "negative")


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

    # Ancho de lectura: a todo el ancho el chevron de los desplegables quedaba a 1300px del nombre.
    # Centrado: pegado a la izquierda dejaba media pantalla vacía a la derecha
    with ui.column().classes("w-full max-w-3xl mx-auto gap-0"):
        encabezado(ui.label(titulo).classes("text-h5 p-4"), 2)
        ui.label(aviso).classes("text-body2 px-4")
        with ui.column().classes("p-4 gap-4 w-full"):
            for clase in listaClases:
                activo = configuracion.get(clase.modulo, False)
                # Una sección por tipo con el divisor al final: antes iba bajo la fila del switch y los aparatos
                # quedaban pegados al tipo siguiente
                with ui.column().classes(f"w-full gap-2 border-b border-{tema.colorOscuro} pb-4"):
                    # no-wrap: en celular una descripción larga bajaba el texto debajo del switch
                    with ui.row().classes("items-center w-full no-wrap"):
                        interruptor = ui.switch(
                            value=activo, on_change=lambda e, c=clase: cambiarEstado(c.modulo, e.value, c.nombre)
                        )
                        interruptor.props["aria-label"] = f"Activar {clase.nombre}"
                        with ui.column().classes("gap-0 min-w-0"):
                            # Junto al nombre y no al final de la fila: en pantallas anchas quedaría lejos del switch
                            with ui.row().classes("items-center gap-x-2 gap-y-0"):
                                encabezado(ui.label(clase.nombre).classes("text-subtitle1 font-bold"), 3)
                                if gui is not None:
                                    pendiente = ui.badge("Pendiente de reinicio", color=tema.colorPendiente, text_color="black")
                                    pendiente.mark(f"pendiente-{clase.modulo}")
                                    # También por sus aparatos u opciones editados (claves "<archivo>:..." y "<archivo>"):
                                    # sus desplegables no tienen lugar para la etiqueta y así se sabe qué tipo espera
                                    claves = (f"{archivo}.{clase.modulo}", getattr(clase, "archivoConfiguracion", None) or "-")
                                    pendiente.bind_visibility_from(
                                        gui,
                                        "pendientesReinicio",
                                        backward=lambda p, c=claves: any(k in (c[0], c[1]) or k.startswith(f"{c[1]}:") for k in p),
                                    )
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

    def campos(contenedor: dict, propiedades: list[propiedadAccion], marca: str) -> None:
        with ui.row().classes("items-start gap-4 p-2"):
            for propiedad in propiedades:
                if not propiedad.elementos:
                    campoPropiedad(contenedor, propiedad, marca, editores)
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

    with ui.column().classes(f"{CONTENIDO_TIPO} gap-1"):
        with ui.expansion("Configuración", caption=archivo, icon="settings") as desplegable:
            desplegable.classes("w-full").props(DESPLEGABLE_LIGERO)
            formulario()
            guardarBoton = ui.button("Guardar", icon="save", color=tema.colorOscuro, on_click=guardar)
            guardarBoton.classes("m-2").mark(f"guardar-{clase.modulo}")




def mostrarAparatos(clase: type[dispositivo], gui=None, interruptor: ui.switch | None = None) -> None:
    """Lista los aparatos de un tipo (ej. teclados.md) con un desplegable para editar el nombre

    Las clases con listarDisponibles (teclados, pedal) además se pueden agregar y quitar sin reiniciar, si hay gui.
    Las de grupos (StreamDeck, con listaDeModelo) crean grupos vacíos y adentro se agregan, ordenan y quitan
    los StreamDeck; cada cambio reconecta solo ese grupo
    """
    archivo = clase.archivoConfiguracion
    # Sin aparato que buscar (MQTT) se agrega llenando sus propiedadesAparato
    agregable = gui is not None and (hasattr(clase, "listarDisponibles") or bool(clase.propiedadesAparato))
    conGrupos = hasattr(clase, "listaDeModelo")
    abierto: dict = {}
    "Grupo que se acaba de crear o cambiar (se dibuja abierto) y botón que tenía el foco, el refresh los recrea"

    def guardar(data: dict, nombre: ui.input, internos: list, etiqueta: ui.item_label) -> None:
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
        cambióNombre = nombreNuevo != nombreAnterior or any(d["nombre"] != e.value.strip() for d, e in internos)
        data["nombre"] = nombreNuevo
        for dataInterno, editor in internos:
            dataInterno["nombre"] = editor.value.strip()
        # Se reemplaza su entrada en el archivo leído ahora, por si se agregó o quitó otro aparato desde que se dibujó
        SalvarArchivo(archivo, [data if otro.get("nombre") == nombreAnterior else otro for otro in aparatos])
        etiqueta.text = nombreNuevo
        # Los nombres se usan al cargar (pestañas, acciones con 'dispositivo'); el resto lo aplica el aparato si puede
        conectado = [d for d in (gui.listaDispositivos if gui else []) if d.nombre == nombreAnterior]
        if not cambióNombre and conectado and all(d.aplicarAparato(data) for d in conectado):
            ui.notify(f"{nombreNuevo} guardado y aplicado", type="positive")
            return
        marcarPendiente(gui, f"{archivo}:{data.get('dispositivo', nombreAnterior)}", f"{nombreNuevo} editado")
        ui.notify(f"{nombreNuevo} guardado; se aplica al reiniciar ElGarrobo", type="positive")

    def agregar(data: dict) -> None:
        # Pestaña al final: se ordenan de mayor a menor ordenar
        data["ordenar"] = min((d.nivelOrdenar for d in gui.listaDispositivos), default=1) - 1
        SalvarArchivo(archivo, (ObtenerArchivo(archivo) or []) + [data])
        nuevo = gui.agregarDispositivo(clase, data)
        # MQTT no tiene archivo de acciones: las recibe por su topic de control
        if data.get("archivo") and not nuevo.tieneFolder("/"):
            nuevo.crearFolder("/")
        if conGrupos:
            abierto.update(grupo=data["nombre"], marca=None)
            ui.notify(f"Grupo {data['nombre']} creado; agrega sus StreamDeck", type="positive")
        else:
            ui.notify(f"{data['nombre']} agregado y conectado; asigna sus teclas en su pestaña de Acciones", type="positive")
        lista.refresh()

    def reconectarGrupo(data: dict, aviso: str, marca: str | None = None) -> None:
        """Guarda el grupo y lo vuelve a conectar con sus StreamDeck, así el cambio se aplica sin reiniciar"""
        SalvarArchivo(archivo, [data if otro.get("nombre") == data["nombre"] else otro for otro in ObtenerArchivo(archivo) or []])
        gui.quitarDispositivo(data["nombre"])
        gui.agregarDispositivo(clase, data)
        abierto.update(grupo=data["nombre"], marca=marca)
        ui.notify(aviso, type="positive")
        lista.refresh()

    def moverDeck(data: dict, decks: list, desde: int, hacia: int, marca: str) -> None:
        decks[desde], decks[hacia] = decks[hacia], decks[desde]
        reconectarGrupo(data, f"{decks[hacia]['nombre']}: posición {hacia + 1} de {len(decks)}", marca)

    def quitarDeck(data: dict, decks: list, posición: int) -> None:
        quitado = decks.pop(posición)
        reconectarGrupo(data, f"{quitado['nombre']} quitado de {data['nombre']}")

    def abrirAgregarDeck(data: dict) -> None:
        def alGuardar(nuevo: dict) -> None:
            modelo = asistenteDeck.disponibles.get(nuevo["dispositivo"], "")
            data.setdefault(clase.listaDeModelo(modelo), []).append(nuevo)
            reconectarGrupo(data, f"{nuevo['nombre']} agregado a {data['nombre']}")

        grupos = ObtenerArchivo(archivo) or []
        decks = [d for grupo in grupos for valor in grupo.values() if isinstance(valor, list) for d in valor if isinstance(d, dict)]
        nombres = {str(d.nombre).lower() for d in gui.listaDispositivos} | {str(a.get("nombre")).lower() for a in grupos + decks}
        asistenteDeck.alGuardar = alGuardar
        asistenteDeck.abrir({d.get("dispositivo") for d in decks}, nombres)

    def quitar(nombre: str) -> None:
        SalvarArchivo(archivo, [data for data in ObtenerArchivo(archivo) or [] if data.get("nombre") != nombre])
        gui.quitarDispositivo(nombre)
        ui.notify(f"{nombre} quitado, su archivo de acciones se conserva")
        lista.refresh()

    def mostrarDistribucion(data: dict) -> None:
        """Distribución del teclado con su miniatura y el mismo diálogo de la barra de Acciones para cambiarla"""
        from elGarrobo.dispositivos.miteclado.mi_teclado_macro import cargarDistribucion

        def alElegir(elegido: dispositivo) -> None:
            # data se vuelve a guardar con Guardar: sin esto regresaría la distribución anterior
            if elegido.distribucion:
                data["distribucion"] = elegido.distribucion
            else:
                data.pop("distribucion", None)
            # El conectado se busca por ruta: si le cambiaron el nombre sigue con el anterior hasta reiniciar
            for conectado in gui.listaDispositivos if gui else []:
                if type(conectado) is clase and conectado.dispositivo == data.get("dispositivo"):
                    conectado.distribucion = elegido.distribucion
            fila.refresh()

        def abrir() -> None:
            dialogoDistribuciones.alElegir = alElegir
            # Instancia aparte y no la conectada: cambiarDistribucion guarda por nombre y el de data es el del archivo
            dialogoDistribuciones.abrir(clase(data))

        @ui.refreshable
        def fila() -> None:
            nombre = data.get("distribucion")
            teclas = cargarDistribucion(nombre) if nombre else None
            with ui.row().classes("items-center gap-x-4 gap-y-2 px-2"):
                with ui.column().classes("gap-0"):
                    ui.label("Distribución").classes("text-caption")
                    ui.label(nombre or "Ninguna, sus teclas se ven como lista")
                if teclas:
                    miniatura(teclas, unidad=6)
                boton = ui.button("Cambiar", icon="keyboard", on_click=abrir).props("flat no-caps")
                boton.props["aria-label"] = f"Cambiar distribución de {data.get('nombre', '')}"
                boton.mark(f"cambiarDistribucion-{data.get('nombre')}")

        fila()

    def abrirAgregar() -> None:
        aparatos = ObtenerArchivo(archivo) or []
        nombres = {str(d.nombre).lower() for d in gui.listaDispositivos} | {str(a.get("nombre")).lower() for a in aparatos}
        asistente.abrir({a.get("dispositivo") for a in aparatos}, nombres)

    @ui.refreshable
    def lista() -> None:
        aparatos = ObtenerArchivo(archivo) or []
        if not aparatos:
            # Qué falta y cómo agregarlo: el nombre del archivo solo no le dice nada a quien no edita .md
            with ui.row().classes("items-center no-wrap gap-3 py-1").mark(f"vacio-{clase.modulo}"):
                ui.icon(clase.icono, size="sm").classes("opacity-60")
                with ui.column().classes("gap-0 min-w-0"):
                    ui.label(f"Aún no hay ningún {clase.nombre}")
                    if agregable and conGrupos:
                        como = "Presiona Agregar grupo y luego agrega sus StreamDeck"
                    elif agregable and hasattr(clase, "listarDisponibles"):
                        como = f"Conecta uno y presiona {textoAgregar}"
                    elif agregable:
                        como = f"Presiona {textoAgregar}"
                    else:
                        # Sin gui no se puede conectar al momento
                        ruta = str(Path(ObtenerFolderConfig(), archivo)).replace(str(Path.home()), "~", 1)
                        como = f"Por ahora se agrega a mano en {ruta}"
                    ui.label(como).classes("text-caption break-words")
        chips = []
        for data in aparatos:
            titulo, ruta = data.get("nombre", "Sin nombre"), data.get("dispositivo", "")
            caption = "Grupo de StreamDeck" if conGrupos else clase.nombreAparato(ruta)
            with ui.expansion(titulo, value=abierto.get("grupo") == titulo) as desplegable:
                desplegable.classes("w-full").props(DESPLEGABLE_LIGERO)
                # Cabecera propia para el estado: la de Quasar solo tiene ícono, nombre y caption.
                # Junto al caption y no a la derecha: en celular le quitaba ancho y el caption bajaba palabra por palabra
                with desplegable.add_slot("header"):
                    with ui.item_section().props("avatar"):
                        ui.icon(clase.icono)
                    with ui.item_section():
                        etiqueta = ui.item_label(titulo)
                        with ui.row().classes("items-center gap-x-3 gap-y-0"):
                            if gui is not None:
                                with ui.row().classes("items-center no-wrap gap-1").mark(f"estado-{titulo}"):
                                    punto = ui.element("span").classes("w-2 h-2 rounded-full shrink-0")
                                    texto = ui.label().classes("text-caption")
                                chips.append((data, punto, texto))
                            ui.item_label(caption).props("caption")
                nombre = ui.input("Nombre", value=data.get("nombre", "")).classes("p-2")
                if conDistribucion:
                    mostrarDistribucion(data)
                if clase.propiedadesAparato:
                    with ui.row().classes("items-start gap-4 px-2"):
                        marca = f"{clase.modulo}-{titulo}"
                        editores = [campoPropiedad(data, p, marca, []) for p in clase.propiedadesAparato]
                    nota = ui.label(clase.notaAparato(data)).classes("text-caption px-2")
                    for editor in editores:
                        editor.on_value_change(lambda _, d=data, n=nota: n.set_text(clase.notaAparato(d)))
                # Aparatos dentro de otro, ej. los StreamDeck de deck_combinado.md (streamDecks / streamDecksPlus)
                internos = [
                    (valor, posición, interno)
                    for valor in data.values()
                    if isinstance(valor, list)
                    for posición, interno in enumerate(valor)
                    if isinstance(interno, dict) and "nombre" in interno
                ]
                editoresInternos = []
                ordenable = conGrupos and agregable
                if internos:
                    ui.label("StreamDeck del grupo, en el orden de sus teclas" if conGrupos else "Aparatos internos").classes("text-caption px-2")
                for decks, posición, interno in internos:
                    with ui.row().classes("items-center gap-1 px-2 no-wrap w-full max-w-md"):
                        etiqueta = f"Nombre · {interno.get('dispositivo', '')}"
                        editor = ui.input(etiqueta, value=interno["nombre"]).classes("grow")
                        editoresInternos.append((interno, editor))
                        if ordenable:
                            botonesDeck(data, decks, posición, interno["nombre"])
                if ordenable:
                    if not internos:
                        ui.label("Grupo vacío: agrega el primer StreamDeck").classes("text-caption px-2")
                    botonDeck = ui.button("Agregar StreamDeck", icon="add", on_click=lambda d=data: abrirAgregarDeck(d))
                    botonDeck.props("flat no-caps").classes("mx-2").mark(f"agregarDeck-{titulo}")
                with ui.row().classes("m-2"):
                    ui.button(
                        "Guardar",
                        icon="save",
                        color=tema.colorOscuro,
                        on_click=lambda d=data, n=nombre, i=editoresInternos, e=etiqueta: guardar(d, n, i, e),
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

        def actualizarEstados() -> None:
            tipoActivo = interruptor.value if interruptor is not None else True
            for data, punto, texto in chips:
                ruta = data.get("dispositivo")
                # Por ruta además del nombre: renombrado sigue cargado con el anterior hasta reiniciar
                cargados = (d for d in gui.listaDispositivos if type(d) is clase)
                instancia = next((d for d in cargados if d.nombre == data.get("nombre") or (ruta and d.dispositivo == ruta)), None)
                estado, color = estadoAparato(instancia, tipoActivo)
                texto.set_text(estado)
                punto.classes(replace=f"w-2 h-2 rounded-full shrink-0 bg-{color}")

        if chips:
            actualizarEstados()
            # ponytail: sondeo cada 2 s, los dispositivos no avisan al conectarse; con eventos se quitaría el timer
            ui.timer(2, actualizarEstados)

    conDistribucion = hasattr(clase, "cambiarDistribucion")
    if conGrupos:
        textoAgregar = "Agregar grupo"
    elif hasattr(clase, "listarDisponibles"):
        textoAgregar = f"Agregar {clase.tipo}"
    else:
        textoAgregar = f"Agregar {clase.nombre}"
    if conDistribucion:
        dialogoDistribuciones = dialogoDistribucion(None)
    def botonesDeck(data: dict, decks: list, posición: int, nombre: str) -> None:
        """Subir, bajar y quitar un StreamDeck del grupo; el orden es el de sus teclas"""
        # ponytail: los Plus van en su propia lista y siempre después de los normales, solo se ordenan entre ellos
        for icono, texto, hacia, marca in (("arrow_upward", "Subir", posición - 1, "subir"), ("arrow_downward", "Bajar", posición + 1, "bajar")):
            marca = f"{marca}-{nombre}"
            boton = ui.button(icon=icono, on_click=lambda h=hacia, m=marca: moverDeck(data, decks, posición, h, m))
            boton.props("flat round dense").mark(marca)
            boton.props["aria-label"] = f"{texto} {nombre}"
            if not 0 <= hacia < len(decks):
                # Invisible y no solo deshabilitado, como en Ordenar pestañas: así no cambia el ancho
                boton.disable()
                boton.classes("invisible")
            elif abierto.get("marca") == marca:
                # El refresh recrea el botón: se le devuelve el foco para seguir moviendo con el teclado
                ui.run_javascript(f"setTimeout(() => getHtmlElement({boton.id})?.focus(), 50)")
        quitarBoton = ui.button(
            icon="delete",
            color=tema.colorPeligro,
            on_click=lambda: pregunta.preguntar(f"¿Quitar {nombre} de {data['nombre']}?", "Quitar", lambda: quitarDeck(data, decks, posición)),
        )
        quitarBoton.props("flat round dense").mark(f"quitarDeck-{nombre}")
        quitarBoton.props["aria-label"] = f"Quitar {nombre}"

    if agregable:
        if conGrupos:
            asistente = dialogoAgregar("Nuevo grupo de StreamDeck", agregar, prefijoArchivo="streamdeck")
            asistenteDeck = dialogoAgregar("Agregar StreamDeck", None, clase.listarDisponibles)
        elif hasattr(clase, "listarDisponibles"):
            asistente = dialogoAgregar(textoAgregar, agregar, clase.listarDisponibles, clase.tipo, conDistribucion)
        else:
            asistente = dialogoAgregar(textoAgregar, agregar, propiedades=clase.propiedadesAparato)
        pregunta = dialogoPregunta()
    with ui.column().classes(f"{CONTENIDO_TIPO} gap-2"):
        lista()
        if agregable:
            with ui.row().classes("items-center gap-x-3 gap-y-1"):
                boton = ui.button(textoAgregar, icon="add", color=tema.colorOscuro, on_click=abrirAgregar)
                boton.mark(f"agregar-{clase.modulo}")
                if interruptor is not None:
                    # Con el tipo apagado ElGarrobo no carga sus aparatos: no tiene sentido conectar uno suelto.
                    # Texto visible y no tooltip: el botón deshabilitado no recibe foco ni hover en el celular
                    boton.bind_enabled_from(interruptor, "value")
                    motivo = ui.label(f"Activa {clase.nombre} para agregar uno").classes("text-caption")
                    motivo.bind_visibility_from(interruptor, "value", backward=lambda v: not v)
