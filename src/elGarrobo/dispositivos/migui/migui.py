from nicegui import app, ui
from PIL import Image

from elGarrobo.accionesOOP import accionBase
from elGarrobo.dispositivos.dispositivoBase import dispositivoBase
from elGarrobo.dispositivos.mideck.mi_deck_imagen import ObtenerImagen
from elGarrobo.miLibrerias import ConfigurarLogging

# librería https://nicegui.io/
# estilo https://tailwindcss.com/
# iconos https://fonts.google.com/icons

logger = ConfigurarLogging(__name__)


class miGui(dispositivoBase):
    """
    Interface Web del ElGarrobo
    """

    listaDispositivos: list[dispositivoBase]

    def __init__(self):

        self.folder: str = "?"
        self.folderLabel = None
        self.listaDispositivosVieja: list = list()
        self.listaAcciones: list = list()
        self.listaAccionesOPP: dict = dict()
        self.salvarAcciones: callable = None
        self.actualizarIconos: callable = None
        self.ejecutaEvento: callable = None
        self.accionEditar: dict = None
        self.opcionesEditar = None
        self.pestañas = None
        self.paneles = None
        self.editorAcción = None

        self.listaDispositivos = list()
        self.tipo = "GUI"

        @ui.page("/")
        def paginaAcciones():
            with ui.splitter(value=20, limits=(15, 50)).classes("w-full") as splitter:
                with splitter.before:
                    self.mostraFormulario()
                with splitter.after:
                    # Contenedor para la tabla
                    self.pestañas = ui.tabs().classes("w-full bg-teal-700 text-white")
                    self.paneles = ui.tab_panels(self.pestañas).classes("w-full")
                    self.mostrarPestañas()
            self.estructura()

        @ui.page("/modulos")
        def paginaModulos():
            ui.label("Pagina Módulos")
            self.estructura()

        @ui.page("/dispositivos")
        def paginaDispositivos():
            ui.label("Pagina Dispositivos")
            self.estructura()

    def mostraFormulario(self):
        def agregarAcción():
            nombre = self.editorNombre.value
            tecla = self.editorTecla.value
            acción = self.editorAcción.value
            for AtributoAccion in self.listaAccionesOPP.keys():
                objetoClase = self.listaAccionesOPP[AtributoAccion]()
                if objetoClase.nombre == acción:
                    acción = objetoClase.comando
                    break
            titulo = self.editorTitulo.value
            nombreDispositivo = self.pestañas.value

            if not (nombre and tecla and acción and nombreDispositivo):
                if not nombreDispositivo:
                    ui.notify(f"Selecciones un dispositivo")
                elif not nombre:
                    ui.notify(f"Ingrese un nombre")
                elif not tecla:
                    ui.notify(f"Ingrese una tecla")
                elif not acción:
                    ui.notify(f"Seleccione una acción")
                return

            tipo = self.tipoDispositivoSeleccionado()
            if tipo in ["steamdeck", "padal"]:
                try:
                    tecla = int(tecla) - 1
                except:
                    ui.notify("Error con tecla no numero")
                    return

            for dispositivo in self.listaDispositivosVieja:
                if dispositivo.get("nombre") == nombreDispositivo:
                    tipoDispositivo = dispositivo.get("tipo")
                    if tipoDispositivo in ["steamdeck", "pedal"]:
                        try:
                            tecla = int(tecla)
                        except ValueError:
                            ui.notify(f"Tecla tiene que ser un numero para {nombreDispositivo}")
                            return
                    accionesDispositivo = dispositivo.get("acciones")

                    if self.botonAgregar.icon == "edit":
                        self.accionEditar["nombre"] = nombre
                        self.accionEditar["key"] = tecla
                        self.accionEditar["accion"] = acción
                        if tipoDispositivo == "steamdeck" and titulo != "":
                            self.accionEditar["titulo"] = titulo

                        if self.opcionesEditar is not None:
                            try:
                                self.accionEditar["opciones"] = obtenerPropiedades(acción)
                            except Exception as e:
                                return

                        ui.notify(f"Editar acción {nombre}")
                        logger.info(f"Editar acción {nombre} a {nombreDispositivo}")
                    else:
                        acciónNueva: dict[str:any] = {"nombre": nombre, "key": tecla, "accion": acción}
                        if tipoDispositivo == "steamdeck" and titulo != "":
                            acciónNueva["titulo"] = titulo
                        accionesDispositivo.append(acciónNueva)

                        if self.opcionesEditar is not None:
                            try:
                                acciónNueva["opciones"] = obtenerPropiedades(acción)
                            except Exception as e:
                                return

                        ui.notify(f"Agregando acción {nombre}")
                        logger.info(f"Agregando acción {nombre} a {nombreDispositivo}")
                    accionesDispositivo.sort(key=lambda x: x.get("key"), reverse=False)
                    folder = dispositivo.get("folder")
                    self.salvarAcciones(accionesDispositivo, dispositivo, folder)
            self.mostrarPestañas()
            self.limpiar_formulario()

        def obtenerPropiedades(acciónSeleccionada: str) -> dict:
            if self.opcionesEditar is not None:
                opciones = dict()
                for opcionesEditor in self.opcionesEditar.keys():
                    objetoEditor = self.opcionesEditar.get(opcionesEditor)
                    valor = objetoEditor.value
                    accionActual = self.listaAccionesOPP[acciónSeleccionada]()
                    for propiedad in accionActual.listaPropiedades:
                        nombrePropiedad = propiedad.nombre
                        if opcionesEditor == nombrePropiedad:
                            obligatorioPropiedad = propiedad.obligatorio
                            if obligatorioPropiedad and valor == "":
                                ui.notify(f"Error {nombrePropiedad} es Obligatorio")
                                logger.warning(f"Error {nombrePropiedad} es Obligatorio")
                                raise Exception("Falta Propiedades")
                            if valor == "":
                                continue
                            opciones[propiedad.atributo] = valor
                return opciones

        with ui.scroll_area().style("height: 75vh"):

            self.editorNombre = ui.input("Nombre").style("width: 200px").props("clearable")
            self.editorTitulo = ui.input("Titulo").style("width: 200px").props("clearable")
            self.editorTitulo.visible = False
            self.editorTecla = ui.input("Tecla").style("width: 200px").props("clearable")
            self.editorAcción = ui.select(options=self.listaAcciones, with_input=True, label="acción", on_change=self.mostrarOpciones).style("width: 200px")
            self.editorDescripcion = ui.label("").style("width: 200px").classes("bg-teal-700 p-2 text-white rounded-lg")
            self.editorDescripcion.visible = False
            self.editorPropiedades = ui.column()
            self.editorOpción = ui.textarea(label="Opciones", placeholder="").style("width: 200px")
            self.editorOpción.visible = False

        with ui.button_group().props("rounded"):
            self.botonAgregar = ui.button(icon="add", color="teal-300", on_click=agregarAcción)
            ui.button(icon="delete", color="teal-300", on_click=self.limpiar_formulario)

    def mostrarOpciones(self):
        self.editorDescripcion.text = ""
        self.editorDescripcion.visible = False
        self.editorPropiedades.clear()
        if self.accionEditar:
            accionOpciones = self.accionEditar.get("accion")
        else:
            accionOpciones = self.editorAcción.value

        for acción in self.listaAccionesOPP.keys():
            claseAccion = self.listaAccionesOPP.get(acción)
            acciónTmp: accionBase = claseAccion()
            if acción == accionOpciones or acciónTmp.nombre == accionOpciones:
                self.editorDescripcion.visible = True
                self.editorDescripcion.text = acciónTmp.descripcion
                with self.editorPropiedades:
                    self.opcionesEditar = dict()
                    for propiedad in acciónTmp.listaPropiedades:
                        nombre = propiedad.nombre
                        etiqueta = nombre
                        ejemplo = propiedad.ejemplo
                        descripción = propiedad.descripcion
                        obligatorio = propiedad.obligatorio
                        if obligatorio:
                            etiqueta = "* " + etiqueta
                        self.opcionesEditar[nombre] = ui.input(label=etiqueta, placeholder=ejemplo)
                        with self.opcionesEditar[nombre]:
                            with ui.button(on_click=lambda d=descripción: ui.notify(d)).props("flat dense"):
                                ui.icon("help", color="teal-300")

    def limpiar_formulario(self):
        self.botonAgregar.icon = "add"
        self.editorNombre.value = ""
        self.editorTecla.value = ""
        self.editorAcción.value = ""
        self.editorOpción.value = ""
        self.editorOpción.visible = False
        self.editorTitulo.value = ""
        self.editorDescripcion.text = ""
        self.editorDescripcion.visible = False
        self.editorPropiedades.clear()
        self.accionEditar = None
        self.opcionesEditar = None

    def mostrarPestañas(self):

        if self.pestañas is None or self.paneles is None:
            return

        self.pestañas.clear()
        self.paneles.clear()

        with self.pestañas:

            for dispositivo in self.listaDispositivos:
                nombre = dispositivo.nombre
                dispositivo.pestaña = ui.tab(dispositivo.nombre)
                dispositivo.pestaña.on("click", self.actualizarEditor)

            for dispositivo in self.listaDispositivosVieja:
                nombre = dispositivo.get("nombre") + " Viejo"
                dispositivo["pestaña"] = ui.tab(nombre)
                dispositivo["pestaña"].on("click", self.actualizarEditor)

        for dispositivo in self.listaDispositivos:
            nombre = dispositivo.nombre
            tipo = dispositivo.tipo
            input = dispositivo.dispositivo
            folder = dispositivo.folder
            clase = dispositivo.clase
            with self.paneles:
                with ui.tab_panel(dispositivo.pestaña).classes("h-svh"):
                    with ui.row():
                        ui.markdown(f"**Tipo**: {tipo}")
                        ui.markdown(f"**clase**: {clase}")
                        ui.markdown(f"**Folder**: {folder}")
                    acciones = dispositivo.listaAcciones

                    with ui.scroll_area().classes("h-96 border border-2 border-teal-600h").style("height: 65vh"):

                        if acciones is None:
                            ui.label("No acciones")
                            continue

                        with ui.row().classes("content p-2"):
                            ui.label("Nombre").style("font-weight: bold; width: 100px")
                            ui.label("Titulo").style("font-weight: bold; width: 100px")
                            # ui.label("Imagen").style("font-weight: bold; width: 150px")
                            ui.label("Tecla").style("font-weight: bold; width: 100px")
                            ui.label("Acción").style("font-weight: bold; width: 125px")
                            ui.label("Opciones").style("font-weight: bold; width: 180px")

                        for acciónActual in acciones:
                            nombreAcción = acciónActual.get("nombre")
                            teclaAcción = acciónActual.get("key")
                            acciónAcción = acciónActual.get("accion")
                            tituloAcción = acciónActual.get("titulo")
                            imagenAcción = acciónActual.get("imagen")

                            # if tipo in ["steamdeck", "pedal"]:
                            #     teclaAcción = int(teclaAcción) + 1

                            with ui.row().classes("content p-2 border-2 border-teal-600"):
                                ui.label(nombreAcción).style("width: 100px")
                                # if tipo == "steamdeck":
                                ui.label(tituloAcción).style("width: 100px")
                                # ui.image(imagenAcción)

                                imagenAcción = self.obtenerRutaImagen(imagenAcción, folder)
                                if imagenAcción is not None:
                                    # ui.label(imagenAcción).style("width: 150px")
                                    pass
                                else:
                                    pass
                                    # ColorFondo = "black"
                                    # image: Image = Image.new("RGB", [100, 100], color=ColorFondo)
                                    # ObtenerImagen(image, acciónActual, folder)

                                    # imagen = ui.image(image).classes("w-12").style("width: 150px")
                                    # imagen.on("click", lambda a=acciónActual: self.seleccionarAcción(a))
                                    # ui.label("").style("width: 150px")

                                ui.label(teclaAcción).style("width: 100px")

                                claseAcción = self.obtenerAcciónOop(acciónAcción)
                                if claseAcción is None:
                                    ui.label(f"{acciónAcción}-vieja").style("width: 125px")
                                    # TODO: montar función viejas
                                else:
                                    objetoAcción = claseAcción()
                                    nombreClase = objetoAcción.nombre
                                    ui.label(f"{nombreClase}").style("width: 125px")

                                with ui.button_group().props("rounded"):
                                    ui.button(icon="play_arrow", color="teal-500", on_click=lambda a=acciónActual: self.ejecutaEvento(a, True))
                                    ui.button(icon="edit", color="teal-500", on_click=lambda a=acciónActual: self.seleccionarAcción(a))
                                    ui.button(icon="delete", color="teal-500", on_click=lambda a=acciónActual: self.eliminarAcción(a))

        for dispositivo in self.listaDispositivosVieja:
            nombre = dispositivo.get("nombre")
            tipo = dispositivo.get("tipo")
            input = dispositivo.get("input")
            clase = dispositivo.get("clase")
            folder = dispositivo.get("folder")
            with self.paneles:
                with ui.tab_panel(dispositivo.get("pestaña")).classes("h-svh"):
                    with ui.row():
                        ui.markdown(f"**Tipo**: {tipo}")
                        ui.markdown(f"**clase**: {clase}")
                        ui.markdown(f"**Folder**: {folder}")
                    acciones = dispositivo.get("acciones")

                    with ui.scroll_area().classes("h-96 border border-2 border-teal-600h").style("height: 65vh"):

                        if acciones is None:
                            ui.label("No acciones")
                            continue

                        with ui.row().classes("content p-2"):
                            ui.label("Nombre").style("font-weight: bold; width: 100px")
                            # if tipo == "steamdeck":
                            ui.label("Titulo").style("font-weight: bold; width: 100px")
                            ui.label("Imagen").style("font-weight: bold; width: 150px")
                            ui.label("Tecla").style("font-weight: bold; width: 100px")
                            ui.label("Acción").style("font-weight: bold; width: 125px")
                            ui.label("Opciones").style("font-weight: bold; width: 180px")

                        for acciónActual in acciones:
                            nombreAcción = acciónActual.get("nombre")
                            teclaAcción = acciónActual.get("key")
                            acciónAcción = acciónActual.get("accion")
                            tituloAcción = acciónActual.get("titulo")
                            imagenAcción = acciónActual.get("imagen")

                            if tipo in ["steamdeck", "pedal"]:
                                teclaAcción = int(teclaAcción) + 1

                            with ui.row().classes("content p-2 border-2 border-teal-600"):
                                ui.label(nombreAcción).style("width: 100px")
                                # if tipo == "steamdeck":
                                ui.label(tituloAcción).style("width: 100px")
                                # ui.image(imagenAcción)

                                imagenAcción = self.obtenerRutaImagen(imagenAcción, folder)
                                if imagenAcción is not None:
                                    # ui.label(imagenAcción).style("width: 150px")
                                    pass
                                else:
                                    pass
                                    # ColorFondo = "black"
                                    # image: Image = Image.new("RGB", [100, 100], color=ColorFondo)
                                    # ObtenerImagen(image, acciónActual, folder)

                                    # imagen = ui.image(image).classes("w-12").style("width: 150px")
                                    # imagen.on("click", lambda a=acciónActual: self.seleccionarAcción(a))
                                    # ui.label("").style("width: 150px")

                                ui.label(teclaAcción).style("width: 100px")

                                claseAcción = self.obtenerAcciónOop(acciónAcción)
                                if claseAcción is None:
                                    ui.label(f"{acciónAcción}-vieja").style("width: 125px")
                                    # TODO: montar función viejas
                                else:
                                    objetoAcción = claseAcción()
                                    nombreClase = objetoAcción.nombre
                                    ui.label(f"{nombreClase}").style("width: 125px")

                                with ui.button_group().props("rounded"):
                                    ui.button(icon="play_arrow", color="teal-500", on_click=lambda a=acciónActual: self.ejecutaEvento(a, True))
                                    ui.button(icon="edit", color="teal-500", on_click=lambda a=acciónActual: self.seleccionarAcción(a))
                                    ui.button(icon="delete", color="teal-500", on_click=lambda a=acciónActual: self.eliminarAcción(a))

        if self.actualizarIconos is not None:
            self.actualizarIconos()

        for dispositivo in self.listaDispositivosVieja:
            nombreDispositivo = dispositivo.get("nombre")
            tipo = dispositivo.get("tipo")
            self.paneles.value = nombreDispositivo
            self.paneles.update()
            if tipo == "steamdeck":
                self.editorTitulo.visible = True
            return

    def seleccionarAcción(self, accion):
        self.accionEditar = accion
        self.botonAgregar.icon = "edit"
        self.editorNombre.value = accion.get("nombre")
        tipo = self.tipoDispositivoSeleccionado()
        if tipo in ["steamdeck", "pedal"]:
            self.editorTecla.value = int(accion.get("key")) + 1
        else:
            self.editorTecla.value = accion.get("key")

        claseAcción = self.obtenerAcciónOop(accion.get("accion"))
        if claseAcción is None:
            self.editorAcción.value = accion.get("accion")
        else:
            objetoClase = claseAcción()
            self.editorAcción.value = objetoClase.nombre
        self.mostrarOpciones()
        textoOpciones = ""
        opcionesActuales = accion.get("opciones")
        self.editorOpción.visible = False

        if opcionesActuales:

            claseAcción = self.listaAccionesOPP.get(self.accionEditar.get("accion"))
            if claseAcción is not None:

                objetoClase = claseAcción()
                listaPropiedades = objetoClase.listaPropiedades
                if isinstance(opcionesActuales, dict):
                    for propiedadAccion in opcionesActuales.keys():
                        for propiedad in listaPropiedades:
                            if propiedad.atributo == propiedadAccion:
                                objetoPropiedad = self.opcionesEditar.get(propiedad.nombre)
                                objetoPropiedad.value = opcionesActuales.get(propiedadAccion)
            else:
                self.editorOpción.visible = True
                if isinstance(opcionesActuales, dict):
                    for opcionInterna in opcionesActuales.keys():
                        valorOpcion = opcionesActuales.get(opcionInterna)
                        textoOpciones = textoOpciones + f"{opcionInterna}: {valorOpcion}, "

                self.editorOpción.value = textoOpciones

        tipo = self.tipoDispositivoSeleccionado()

        if tipo == "steamdeck":
            self.editorTitulo.value = accion.get("titulo")

    def actualizarEditor(self) -> None:
        tipo = self.tipoDispositivoSeleccionado()

        if tipo == "steamdeck":
            self.editorTitulo.visible = True
        else:
            self.editorTitulo.visible = False
        self.limpiar_formulario()

    def tipoDispositivoSeleccionado(self) -> str:
        nombreDispositivo = self.pestañas.value
        for dispositivo in self.listaDispositivosVieja:
            if dispositivo.get("nombre") == nombreDispositivo:
                return dispositivo.get("tipo")

    def eliminarAcción(self, accion):
        nombreDispositivo = self.pestañas.value
        for dispositivo in self.listaDispositivosVieja:
            if dispositivo.get("nombre") == nombreDispositivo:
                tipo = dispositivo.get("tipo")

        if nombreDispositivo is None:
            ui.notify(f"Falta seleccionar dispositivo")
            return

        for dispositivo in self.listaDispositivosVieja:
            if dispositivo.get("nombre") == nombreDispositivo:
                acciones = dispositivo.get("acciones")
                acciones.remove(accion)
                folder = dispositivo.get("folder")
                self.salvarAcciones(acciones, dispositivo, folder)
                ui.notify(f"Se elimino la accion {accion.get('nombre')}")
                self.mostrarPestañas()

    def estructura(self):
        with ui.header(elevated=True).classes("bg-teal-900 items-center justify-between").style("height: 5vh; padding: 1px"):
            ui.label("ElGarrobo").classes("text-h5")
            with ui.row():
                ui.markdown("**FolderRuta**:")
                self.folderLabel = ui.markdown(self.folder)
            with ui.button(icon="menu").props("flat color=white"):
                with ui.menu() as menu:
                    ui.menu_item("Acciones", on_click=lambda: ui.navigate.to("/"))
                    ui.menu_item("Módulos", on_click=lambda: ui.navigate.to("/modulos"))
                    ui.menu_item("Dispositivos", on_click=lambda: ui.navigate.to("/dispositivos"))

        with ui.footer().classes("bg-teal-900").style("height: 5vh; padding: 1px"):
            with ui.row().classes("w-full"):
                ui.label("Creado por ChepeCarlos")
                ui.space()
                ui.link("Youtube", "https://www.youtube.com/@chepecarlo")
                ui.link("Tiktok", "https://www.tiktok.com/@chepecarlo")

    def iniciar(self):

        logger.info("Iniciando GUI")
        ui.run(title="ElGarrobo", reload=False, show=False, dark=True, language="es", uvicorn_logging_level="warning", favicon="🦎")

        # interesante native=True para app
        # ui.run(uvicorn_logging_level="debug", reload=False)

    def desconectar(self) -> None:
        logger.info("Saliendo de NiceGUI")
        app.shutdown()

    def actualizarFolder(self, folder: str):
        self.folder = folder
        if self.folderLabel is not None:
            self.folderLabel.content = self.folder

    def agregarDispositivos(self, dispositivo):
        dispositivo["acciones"] = None
        for dispositivoActual in self.listaDispositivosVieja:
            if dispositivoActual.get("nombre") == dispositivo.get("nombre"):
                return
        logger.info(f"GUI agregando Dispositivo: {dispositivo.get('nombre')}")
        self.listaDispositivosVieja.append(dispositivo)
        self.mostrarPestañas()

    def agregarAcciones(self, listaAcciones: list):
        for accion in listaAcciones:
            self.listaAcciones.append(accion)
        self.listaAcciones.sort()
        if self.editorAcción is not None:
            self.editorAcción.options = self.listaAcciones
            self.editorAcción.update()

    def actualizarAcciones(self, nombreDispositivo: str, acciones: list, folder: str):
        for dispositivo in self.listaDispositivosVieja:
            if dispositivo.get("nombre") == nombreDispositivo:
                dispositivo["acciones"] = acciones
                dispositivo["folder"] = folder
        self.mostrarPestañas()

    def obtenerAcciónOop(self, comandoAcción: str):
        if comandoAcción in self.listaAccionesOPP:
            return self.listaAccionesOPP[comandoAcción]
        return None

    def obtenerRutaImagen(self, Imagen: str, folder: str):
        if Imagen is None:
            return
        pass
