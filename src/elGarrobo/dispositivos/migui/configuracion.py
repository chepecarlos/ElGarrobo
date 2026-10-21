"""Páginas de configuración de la GUI: /modulos, /dispositivos y /configurar

Funciones sin estado: cada página arma sus widgets al abrirse, así cada pestaña del navegador tiene los suyos
"""

from nicegui import ui

from elGarrobo import servicio
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.editores import encabezado, marcarError
from elGarrobo.miLibrerias import ObtenerArchivo, SalvarArchivo, SalvarValor, leerData


def mostrarListaActivables(titulo: str, archivo: str, listaClases: list) -> None:
    """Lista módulos o dispositivos con un switch para activarlos/desactivarlos

    Args:
        titulo (str): Título de la página
        archivo (str): Archivo de configuración ("modulos" o "dispositivos")
        listaClases (list): Clases con atributos `modulo`, `nombre` y `descripcion`
    """
    configuracion = leerData(archivo) or {}

    def cambiarEstado(clave: str, valor: bool, nombre: str) -> None:
        SalvarValor(archivo, clave, valor)
        ui.notify(f"{nombre} {'activado' if valor else 'desactivado'}. Reinicia ElGarrobo para aplicarlo")

    encabezado(ui.label(titulo).classes("text-h5 p-4"), 2)
    ui.label("Los cambios se aplican al reiniciar ElGarrobo (menú → Reiniciar)").classes(f"text-caption px-4 text-{tema.colorClaro}")
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
                mostrarAparatos(clase)
            elif getattr(clase, "propiedades", None):
                mostrarConfiguracionModulo(clase)


def mostrarConfigurar() -> None:
    """Opciones generales de ElGarrobo, por ahora solo el arranque automático al iniciar sesión"""

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


def mostrarAparatos(clase: type[dispositivo]) -> None:
    """Lista los aparatos de un tipo (ej. teclados.md) con un desplegable para editar nombre y orden"""
    archivo = clase.archivoConfiguracion
    aparatos = ObtenerArchivo(archivo) or []

    def guardar(data: dict, nombre: ui.input, orden: ui.number, internos: list, desplegable: ui.expansion) -> None:
        nombreNuevo = (nombre.value or "").strip()
        error = None
        # elGarrobo busca dispositivos por nombre sin importar mayúsculas (ej. entrar_folder con 'dispositivo')
        if any(otro is not data and str(otro.get("nombre")).lower() == nombreNuevo.lower() for otro in aparatos):
            error = f"Ya existe {nombreNuevo}"
        marcarError(nombre, "El nombre no puede quedar vacío" if not nombreNuevo else error)
        vacíos = [editor for _, editor in internos if not (editor.value or "").strip()]
        for _, editor in internos:
            marcarError(editor, "Falta el nombre" if editor in vacíos else None)
        if not nombreNuevo or error or vacíos:
            return
        data["nombre"] = nombreNuevo
        data["ordenar"] = int(orden.value or 0)
        for dataInterno, editor in internos:
            dataInterno["nombre"] = editor.value.strip()
        SalvarArchivo(archivo, aparatos)
        desplegable.text = nombreNuevo
        ui.notify(f"{nombreNuevo} guardado. Reinicia ElGarrobo para aplicarlo", type="positive")

    with ui.column().classes("w-full pl-12 gap-1"):
        if not aparatos:
            ui.label(f"No hay aparatos en {archivo}").classes("text-caption")
        for data in aparatos:
            titulo, ruta = data.get("nombre", "Sin nombre"), data.get("dispositivo", "")
            with ui.expansion(titulo, caption=ruta, icon=clase.icono) as desplegable:
                desplegable.classes(f"w-full border border-{tema.colorOscuro} rounded")
                with ui.row().classes("items-start gap-4 p-2"):
                    nombre = ui.input("Nombre", value=data.get("nombre", ""))
                    orden = ui.number("Orden", value=data.get("ordenar", 0), precision=0).classes("w-24")
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
                ui.button(
                    "Guardar",
                    icon="save",
                    color=tema.colorOscuro,
                    on_click=lambda d=data, n=nombre, o=orden, i=editoresInternos, e=desplegable: guardar(
                        d, n, o, i, e
                    ),
                ).classes("m-2")
