from nicegui import ui

# librería https://nicegui.io/
# estilo https://tailwindcss.com/
# iconos https://fonts.google.com/icons


class miGui:
    """
    Interface Web del ElGarrobo
    """

    def __init__(self):

        self.folder: str = "?"
        self.folderLabel = None
        self.listaDispositivos: list = list()
        self.listaAcciones: list = list()
        self.salvarAcciones: callable = None
        self.actualizarIconos: callable = None

        with ui.splitter(value=20).classes("w-full") as splitter:
            with splitter.before:
                self.mostraFormulario()
            with splitter.after:
                # Contenedor para la tabla
                self.pestañas = ui.tabs().classes("w-full bg-teal-700 text-white")
                self.paneles = ui.tab_panels(self.pestañas).classes("w-full")
                self.mostrarPestañas()

        self.estructura()

    def mostraFormulario(self):
        def agregarAcción():
            nombre = self.editorNombre.value
            tecla = self.editorTecla.value
            acción = self.editorAcción.value
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

            for dispositivo in self.listaDispositivos:
                if dispositivo.get("nombre") == nombreDispositivo:
                    tipoDispositivo = dispositivo.get("tipo")
                    if tipoDispositivo == "steamdeck":
                        try:
                            tecla = int(tecla)
                        except ValueError:
                            ui.notify(f"Tecla tiene que ser un numero para {nombreDispositivo}")
                            return
                    accionesDispositivo = dispositivo.get("acciones")
                    acciónNueva: dict[str:any] = {"nombre": nombre, "key": tecla, "accion": acción}

                    if tipoDispositivo == "steamdeck" and self.editorTitulo != "":
                        acciónNueva["titulo"] = self.editorTitulo.value

                    accionesDispositivo.append(acciónNueva)
                    accionesDispositivo.sort(key=lambda x: x.get("key"), reverse=False)
                    folder = dispositivo.get("folder")
                    self.salvarAcciones(accionesDispositivo, dispositivo, folder)
            ui.notify(f"Agregando acción {nombre}")
            print(f"Agregando acción {nombre} a {nombreDispositivo}")
            self.mostrarPestañas()
            self.limpiar_formulario()

        self.editorNombre = ui.input("Nombre").style("width: 200px")
        self.editorTitulo = ui.input("Titulo").style("width: 200px")
        self.editorTitulo.visible = False
        self.editorTecla = ui.input("Tecla").style("width: 200px")
        self.editorAcción = ui.select(self.listaAcciones, label="acción").style("width: 200px")
        self.editorOpción = ui.textarea(label="Opciones", placeholder="").style("width: 200px")

        with ui.button_group().props("rounded"):
            self.botonAgregar = ui.button(icon="add", color="teal-300", on_click=agregarAcción)
            ui.button(icon="delete", color="teal-300", on_click=self.limpiar_formulario)

    def limpiar_formulario(self):
        self.botonAgregar.icon = "add"
        self.editorNombre.value = ""
        self.editorTecla.value = ""
        self.editorAcción.value = ""
        self.editorOpción.value = ""
        self.editorTitulo.value = ""

    def mostrarPestañas(self):

        self.pestañas.clear()
        self.paneles.clear()

        with self.pestañas:

            for dispositivo in self.listaDispositivos:
                nombre = dispositivo.get("nombre")
                dispositivo["pestaña"] = ui.tab(nombre)
                dispositivo["pestaña"].on("click", self.actualizarEditor)

        for dispositivo in self.listaDispositivos:
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

                    with ui.scroll_area().classes("h-96 border border-2 border-teal-600"):

                        if acciones is None:
                            ui.label("No acciones")
                            continue

                        with ui.row().classes("content p-2"):
                            ui.label("Nombre").style("font-weight: bold; width: 100px")
                            if tipo == "steamdeck":
                                ui.label("Titulo").style("font-weight: bold; width: 100px")
                            ui.label("Tecla").style("font-weight: bold; width: 100px")
                            ui.label("Acción").style("font-weight: bold; width: 125px")
                            ui.label("Opciones").style("font-weight: bold; width: 180px")

                        for acciónActual in acciones:
                            nombreAcción = acciónActual.get("nombre")
                            teclaAcción = acciónActual.get("key")
                            acciónAcción = acciónActual.get("accion")
                            tituloAcción = acciónActual.get("titulo")

                            with ui.row().classes("content p-2 border-2 border-teal-600"):
                                ui.label(nombreAcción).style("width: 100px")
                                if tipo == "steamdeck":
                                    ui.label(tituloAcción).style("width: 100px")
                                ui.label(teclaAcción).style("width: 100px")
                                ui.label(acciónAcción).style("width: 125px")
                                with ui.button_group().props("rounded"):
                                    ui.button(icon="edit", color="teal-300", on_click=lambda a=acciónActual: self.seleccionarAcción(a))
                                    ui.button(icon="delete", color="teal-300", on_click=lambda a=acciónActual: self.eliminarAcción(a))
        if self.actualizarIconos is not None:
            self.actualizarIconos()
        # ui.button("Editar", on_click=lambda f=fila: editar_fila(f)).style("width: 70px")

    def seleccionarAcción(self, accion):
        print(accion)
        self.botonAgregar.icon = "edit"
        self.editorNombre.value = accion.get("nombre")
        self.editorTecla.value = accion.get("key")
        self.editorAcción.value = accion.get("accion")
        textoOpciones = ""
        opcionesActuales = accion.get("opciones")
        if opcionesActuales:
            if isinstance(opcionesActuales, dict):
                for opcionInterna in opcionesActuales.keys():
                    textoOpciones = textoOpciones + f"{opcionInterna}: {opcionesActuales.get(opcionInterna)}, "
            elif isinstance(opcionesActuales, list):
                for opcionInterna in opcionesActuales:
                    for opcionesSecundarias in opcionInterna.keys():
                        textoOpciones = textoOpciones + f"{opcionesSecundarias}: {opcionInterna.get(opcionesSecundarias)}, "
        self.editorOpción.value = textoOpciones

        nombreDispositivo = self.pestañas.value
        for dispositivo in self.listaDispositivos:
            if dispositivo.get("nombre") == nombreDispositivo:
                tipo = dispositivo.get("tipo")
                if tipo == "steamdeck":
                    self.editorTitulo.value = accion.get("titulo")

    def actualizarEditor(self):
        nombreDispositivo = self.pestañas.value
        for dispositivo in self.listaDispositivos:
            if dispositivo.get("nombre") == nombreDispositivo:
                tipo = dispositivo.get("tipo")
                if tipo == "steamdeck":
                    self.editorTitulo.visible = True
                else:
                    self.editorTitulo.visible = False
        self.limpiar_formulario()

    def eliminarAcción(self, accion):
        nombreDispositivo = self.pestañas.value
        for dispositivo in self.listaDispositivos:
            if dispositivo.get("nombre") == nombreDispositivo:
                tipo = dispositivo.get("tipo")
                print(tipo)

        if nombreDispositivo is None:
            ui.notify(f"Falta seleccionar dispositivo")
            return

        for dispositivo in self.listaDispositivos:
            if dispositivo.get("nombre") == nombreDispositivo:
                acciones = dispositivo.get("acciones")
                acciones.remove(accion)
                folder = dispositivo.get("folder")
                self.salvarAcciones(acciones, dispositivo, folder)
                ui.notify(f"Se elimino la accion {accion.get('nombre')}")
                self.mostrarPestañas()

    def estructura(self):
        with ui.header(elevated=True).classes("bg-teal-900 items-center justify-between"):
            ui.label("ElGarrobo").classes("text-h4")
            with ui.row():
                ui.markdown("**FolderRuta**:")
                self.folderLabel = ui.markdown(self.folder)
            ui.button(on_click=lambda: right_drawer.toggle(), icon="menu").props("flat color=white")

        with ui.right_drawer(fixed=False).style("background-color: #ebf1fa").props("bordered") as right_drawer:
            right_drawer.toggle()
            ui.label("RIGHT DRAWER")

        with ui.footer().classes("bg-teal-900"):
            with ui.row():
                ui.label("Creado por ChepeCarlos")
                ui.space()
                ui.link("Youtube", "https://www.youtube.com/@chepecarlo")
                ui.link("Tiktok", "https://www.tiktok.com/@chepecarlo")

    def iniciar(self):
        ui.run(title="ElGarrobo", reload=False, show=False)
        # ui.run(uvicorn_logging_level="debug", reload=False)

    def actualizarFolder(self, folder: str):
        self.folder = folder
        self.folderLabel.content = self.folder

    def agregarDispositivos(self, dispositivo):
        dispositivo["acciones"] = None
        for dispositivoActual in self.listaDispositivos:
            if dispositivoActual.get("nombre") == dispositivo.get("nombre"):
                return
        print(f"GUI agregando Dispositivo {dispositivo.get('nombre')}")
        self.listaDispositivos.append(dispositivo)
        self.mostrarPestañas()

    def agregarAcciones(self, listaAcciones: dict):
        for accion in listaAcciones:
            self.listaAcciones.append(accion)
        self.listaAcciones.sort()
        self.editorAcción.options = self.listaAcciones
        self.editorAcción.update()

    def actualizarAcciones(self, nombreDispositivo: str, acciones: list, folder: str):
        for dispositivo in self.listaDispositivos:
            if dispositivo.get("nombre") == nombreDispositivo:
                dispositivo["acciones"] = acciones
                dispositivo["folder"] = folder
        self.mostrarPestañas()
