from nicegui import ui

# https://nicegui.io/
# https://tailwindcss.com/


class miGui:
    """
    Interface Web del ElGarrobo
    """

    def __init__(self):

        self.folder: str = "?"
        self.folderLabel = None
        self.listaDispositivos: list = list()
        self.listaAcciones: list = list()
        self.agregarAccion: callable = None

        # Datos de ejemplo para la tabla
        datos = [{"nombre": "Alice", "edad": 25, "ciudad": "Madrid"}, {"nombre": "Bob", "edad": 30, "ciudad": "Barcelona"}, {"nombre": "Carlos", "edad": 35, "ciudad": "Valencia"}]

        # Variable global para almacenar la fila que está siendo editada
        fila_seleccionada = None

        # Función para refrescar la tabla
        def mostrar_tabla():
            tabla_cont.clear()

            # Encabezados de la tabla
            with tabla_cont:
                with ui.row():
                    ui.label("Nombre").style("font-weight: bold; width: 100px")
                    ui.label("Tecla").style("font-weight: bold; width: 50px")
                    ui.label("Acción").style("font-weight: bold; width: 100px")
                    ui.label("Acción").style("font-weight: bold; width: 180px")

                # Crear filas de la tabla con botones en cada una
                for fila in datos:
                    with ui.row().classes("content border-2 border-teal-600"):
                        ui.label(fila["nombre"]).style("width: 100px")
                        ui.label(str(fila["edad"])).style("width: 50px")
                        ui.label(fila["ciudad"]).style("width: 100px")
                        ui.button("Seleccionar", on_click=lambda f=fila: seleccionar_fila(f))  # .style("width: 70px")
                        ui.button("Eliminar", on_click=lambda f=fila: eliminar_fila(f)).style("width: 70px")
                        ui.button("Editar", on_click=lambda f=fila: editar_fila(f)).style("width: 70px")

        # Función para seleccionar una fila
        def seleccionar_fila(fila):
            ui.notify(f"Seleccionaste: {fila['nombre']} de {fila['ciudad']}")

        # Función para eliminar una fila
        def eliminar_fila(fila):
            datos.remove(fila)
            mostrar_tabla()

        # Función para cargar los datos de la fila seleccionada en los campos de edición
        def editar_fila(fila):
            global fila_seleccionada
            fila_seleccionada = fila  # Guardar la fila que se está editando
            # Cargar los datos de la fila en los campos de entrada
            nombre_input.value = fila["nombre"]
            edad_input.value = str(fila["edad"])
            ciudad_input.value = fila["ciudad"]
            ui.notify(f"Editando: {fila['nombre']}")

        # Función para guardar los cambios de la fila editada
        def guardar_cambios():
            if fila_seleccionada:
                fila_seleccionada["nombre"] = nombre_input.value
                fila_seleccionada["edad"] = int(edad_input.value)
                fila_seleccionada["ciudad"] = ciudad_input.value
                mostrar_tabla()
                ui.notify("Cambios guardados")
                limpiar_formulario()

        # Función para agregar una fila nueva
        def agregar_fila():
            nombre = nombre_input.value
            edad = int(edad_input.value)
            ciudad = ciudad_input.value
            if nombre and ciudad:
                datos.append({"nombre": nombre, "edad": edad, "ciudad": ciudad})
                mostrar_tabla()
                ui.notify("Fila agregada")
                limpiar_formulario()

        # Función para limpiar los campos de entrada y la fila seleccionada
        def limpiar_formulario():
            global fila_seleccionada
            fila_seleccionada = None
            nombre_input.value = ""
            edad_input.value = 0
            ciudad_input.value = ""

        # tabla_cont = ui.column()

        with ui.splitter(value=20).classes("w-full") as splitter:
            with splitter.before:
                self.mostraFormulario()
            with splitter.after:
                # Contenedor para la tabla
                self.pestañas = ui.tabs().classes("w-full")
                self.paneles = ui.tab_panels(self.pestañas).classes("w-full")
                self.mostrarPestañas()

        self.estructura()

    def mostraFormulario(self):
        def agregarAcción():
            nombre = self.editorNombre.value
            tecla = self.editorTecla.value
            acción = self.editorAcción.value
            nombreDispositivo = self.pestañas.value
            if nombre and tecla and acción and nombreDispositivo:
                for dispositivo in self.listaDispositivos:
                    if dispositivo.get("nombre") == nombreDispositivo:
                        folder = dispositivo.get("folder")
                        print(nombre, tecla, acción, folder, nombreDispositivo)
                # datos.append({"nombre": nombre, "edad": edad, "ciudad": ciudad})
                accionNueva = {"nombre": nombre, "key": tecla, "accion": acción}
                # self.agregarAccion(accionNueva, dispositivo, folder)
                self.mostrarPestañas()
                ui.notify(f"Agregando acción {nombre}")
                limpiar_formulario()
            else:
                ui.notify("Falta información")

        def limpiar_formulario():
            global fila_seleccionada
            fila_seleccionada = None
            self.botonAgregar.text = "Agregar"
            self.editorNombre.value = ""
            self.editorTecla.value = ""
            self.editorAcción.value = ""
            self.editorOpción.value = ""

        self.editorNombre = ui.input("Nombre")  # .style("width: 100px")
        self.editorTecla = ui.input("Tecla")  # .style("width: 50px")
        self.editorAcción = ui.select(self.listaAcciones, label="acción").style("width: 200px")
        self.editorOpción = ui.textarea(label="Opciones", placeholder="").style("width: 200px")

        with ui.button_group():
            self.botonAgregar = ui.button("Agregar", on_click=agregarAcción)
            ui.button("Limpiar", on_click=limpiar_formulario)

    def mostrarPestañas(self):

        self.pestañas.clear()
        self.paneles.clear()

        with self.pestañas:
            for dispositivo in self.listaDispositivos:
                nombre = dispositivo.get("nombre")
                dispositivo["pestaña"] = ui.tab(nombre)

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

                        with ui.row():
                            ui.label("Nombre").style("font-weight: bold; width: 100px")
                            ui.label("Tecla").style("font-weight: bold; width: 100px")
                            ui.label("Acción").style("font-weight: bold; width: 125px")
                            ui.label("Opciones").style("font-weight: bold; width: 180px")

                        for acciónActual in acciones:
                            nombreAcción = acciónActual.get("nombre")
                            teclaAcción = acciónActual.get("key")
                            acciónAcción = acciónActual.get("accion")

                            with ui.row().classes("content border-2 border-teal-600"):
                                ui.label(nombreAcción).style("width: 100px")
                                ui.label(teclaAcción).style("width: 100px")
                                ui.label(acciónAcción).style("width: 125px")
                                ui.button("Editar", on_click=lambda a=acciónActual: self.seleccionarAcción(a))  # .style("width: 70px")
                                # ui.button("Eliminar", on_click=lambda f=fila: eliminar_fila(f)).style("width: 70px")
                                # ui.button("Editar", on_click=lambda f=fila: editar_fila(f)).style("width: 70px")

    def seleccionarAcción(self, accion):
        print(accion)
        self.botonAgregar.text = "Editar"
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

    def estructura(self):
        with ui.header(elevated=True).style("background-color: #0b4c0d").classes("items-center justify-between"):
            ui.label("ElGarrobo").classes("text-h4")
            with ui.row():
                ui.markdown("**FolderRuta**:")
                self.folderLabel = ui.markdown(self.folder)
            ui.button(on_click=lambda: right_drawer.toggle(), icon="menu").props("flat color=white")

        with ui.right_drawer(fixed=False).style("background-color: #ebf1fa").props("bordered") as right_drawer:
            right_drawer.toggle()
            ui.label("RIGHT DRAWER")

        with ui.footer().style("background-color: #0b4c0d"):
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
        self.listaDispositivos.append(dispositivo)
        self.mostrarPestañas()

    def agregarAcciones(self, listaAcciones: dict):
        for accion in listaAcciones:
            self.listaAcciones.append(accion)
        self.listaAcciones.sort()
        self.editorAcción.options = self.listaAcciones

    def actualizarAcciones(self, nombreDispositivo: str, acciones: list, folder: str):
        for dispositivo in self.listaDispositivos:
            if dispositivo.get("nombre") == nombreDispositivo:
                dispositivo["acciones"] = acciones
                dispositivo["folder"] = folder
        self.mostrarPestañas()
