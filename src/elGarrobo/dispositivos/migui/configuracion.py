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


def mostrarListaActivables(titulo: str, archivo: str, listaClases: list, gui=None) -> None:
    """Lista módulos o dispositivos con un switch para activarlos/desactivarlos

    Args:
        titulo (str): Título de la página
        archivo (str): Archivo de configuración ("modulos" o "dispositivos")
        listaClases (list): Clases con atributos `modulo`, `nombre` y `descripcion`
        gui (miGui): para agregar y quitar aparatos sin reiniciar; sin ella solo se editan
    """
    configuracion = leerData(archivo) or {}

    def cambiarEstado(clave: str, valor: bool, nombre: str) -> None:
        SalvarValor(archivo, clave, valor)
        ui.notify(f"{nombre} {'activado' if valor else 'desactivado'}. Reinicia ElGarrobo para aplicarlo")

    encabezado(ui.label(titulo).classes("text-h5 p-4"), 2)
    ui.label("Los cambios se aplican al reiniciar ElGarrobo (menú → Reiniciar)").classes("text-caption px-4 texto-acento")
    with ui.column().classes("p-4 gap-2 w-full"):
        for clase in listaClases:
            activo = configuracion.get(clase.modulo, False)
            with ui.row().classes(f"items-center w-full border-b border-{tema.colorOscuro} pb-2"):
                interruptor = ui.switch(value=activo, on_change=lambda e, c=clase: cambiarEstado(c.modulo, e.value, c.nombre))
                interruptor.props["aria-label"] = f"Activar {clase.nombre}"
                with ui.column().classes("gap-0"):
                    ui.label(clase.nombre).classes("font-bold")
                    ui.label(clase.descripcion).classes("text-caption")
            # En dispositivos archivoConfiguracion es una lista de aparatos, en módulos un dict de opciones
            if issubclass(clase, dispositivo) and clase.archivoConfiguracion:
                mostrarAparatos(clase, gui, interruptor)
            elif getattr(clase, "propiedades", None):
                mostrarConfiguracionModulo(clase)
    if gui is not None:
        with ui.column().classes("p-4 gap-1 w-full max-w-xl"):
            encabezado(ui.label("Orden de pestañas").classes("text-h6"), 3)
            ui.label("Se aplica al volver a Acciones").classes("text-caption")
            ordenPestañas(gui)


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


@ui.refreshable
def ordenPestañas(gui) -> None:
    """Dispositivos en el orden de sus pestañas con botones para subir y bajar; se guarda al mover"""
    dispositivos = sorted(gui.listaDispositivos, key=lambda d: d.nivelOrdenar, reverse=True)

    def mover(desde: int, hacia: int) -> None:
        dispositivos[desde], dispositivos[hacia] = dispositivos[hacia], dispositivos[desde]
        guardarOrden(dispositivos)
        ordenPestañas.refresh()

    for posición, dispositivoActual in enumerate(dispositivos):
        nombre = dispositivoActual.nombre
        with ui.row().classes(f"items-center w-full no-wrap border-b border-{tema.colorOscuro} py-1"):
            ui.icon(dispositivoActual.icono)
            ui.label(nombre).classes("font-bold grow")
            ui.label(dispositivoActual.tipo).classes("text-caption")
            for icono, texto, hacia, marca in (
                ("arrow_upward", "Subir", posición - 1, "subir"),
                ("arrow_downward", "Bajar", posición + 1, "bajar"),
            ):
                boton = ui.button(icon=icono, on_click=lambda p=posición, h=hacia: mover(p, h)).props("flat round dense")
                boton.props["aria-label"] = f"{texto} {nombre}"
                boton.mark(f"{marca}-{nombre}")
                if not 0 <= hacia < len(dispositivos):
                    # Invisible y no solo deshabilitada: apagada casi no se distingue, y así no cambia el ancho
                    boton.disable()
                    boton.classes("invisible")


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


def mostrarConfiguracionModulo(clase: type) -> None:
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
        ui.notify(f"{clase.nombre} guardado. Reinicia ElGarrobo para aplicarlo", type="positive")

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
        ui.notify(f"{nombreNuevo} guardado. Reinicia ElGarrobo para aplicarlo", type="positive")

    def agregar(data: dict) -> None:
        # Pestaña al final: se ordenan de mayor a menor ordenar
        data["ordenar"] = min((d.nivelOrdenar for d in gui.listaDispositivos), default=1) - 1
        SalvarArchivo(archivo, (ObtenerArchivo(archivo) or []) + [data])
        nuevo = gui.agregarDispositivo(clase, data)
        if not nuevo.tieneFolder("/"):
            nuevo.crearFolder("/")
        ui.notify(f"{data['nombre']} agregado y conectado", type="positive")
        lista.refresh()
        ordenPestañas.refresh()

    def quitar(nombre: str) -> None:
        SalvarArchivo(archivo, [data for data in ObtenerArchivo(archivo) or [] if data.get("nombre") != nombre])
        gui.quitarDispositivo(nombre)
        ui.notify(f"{nombre} quitado, su archivo de acciones se conserva")
        lista.refresh()
        ordenPestañas.refresh()

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
