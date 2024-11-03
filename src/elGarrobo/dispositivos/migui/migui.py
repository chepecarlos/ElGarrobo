from nicegui import ui


class miGui:
    """
    Interface Web del ElGarrobo
    """

    def __init__(self):

        self.folder = "?"
        self.folderLabel = None
        self.listaDispositivos = list()

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

        # Contenedor para la tabla
        self.pestañas = ui.tabs().classes("w-full")
        self.paneles = ui.tab_panels(self.pestañas).classes("w-full")
        tabla_cont = ui.column()

        self.mostrarPestañas()
        # mostrar_tabla()

        # Formulario para agregar o editar una fila
        # with ui.row():
        #     nombre_input = ui.input("Nombre").style("width: 100px")
        #     edad_input = ui.number("Edad").style("width: 50px")
        #     ciudad_input = ui.select(["San Miguel", "San Salvador", "La Union"], value="San Miguel").style("width: 100px")
        #     # ciudad_input = ui.input("Ciudad").style("width: 100px")
        #     ui.button("Agregar", on_click=agregar_fila).style("width: 70px")
        #     ui.button("Guardar cambios", on_click=guardar_cambios).style("width: 120px")

        self.estructura()

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
            with self.paneles:
                with ui.tab_panel(dispositivo.get("pestaña")):
                    with ui.row():
                        ui.markdown(f"**Tipo**: {tipo}")
                        # ui.markdown(f"**Input**: {input}")
                        ui.markdown(f"**clase**: {clase}")

    def estructura(self):
        with ui.header(elevated=True).style("background-color: #0b4c0d").classes("items-center justify-between"):
            ui.label("ElGarrobo").classes("text-h4")
            with ui.row():
                ui.markdown("**FolderRuta**:")
                self.folderLabel = ui.markdown(self.folder)
            ui.button(on_click=lambda: right_drawer.toggle(), icon="menu").props("flat color=white")
        with ui.footer().style("background-color: #0b4c0d"):
            with ui.row():
                ui.label("Creado por ChepeCarlos")
                ui.space()
                ui.link("Youtube", "https://www.youtube.com/@chepecarlo")
                ui.link("Tiktok", "https://www.youtube.com/@chepecarlo")
            # with ui.button_group():
            #     # ui.button("Agregar", on_click=agregar)
            #     # ui.button("Two", on_click=lambda: ui.notify("You clicked Button 2!"))
            #     # ui.button("Three", on_click=lambda: ui.notify("You clicked Button 3!"))
            # ui.label("FOOTER")

        with ui.left_drawer(top_corner=True, bottom_corner=True).style("background-color: #d7e3f4"):
            ui.label("LEFT DRAWER")
        with ui.right_drawer(fixed=False).style("background-color: #ebf1fa").props("bordered") as right_drawer:
            ui.label("RIGHT DRAWER")
        pass

    def iniciar(self):
        ui.run(title="ElGarrobo", reload=False, show=False)
        # ui.run(uvicorn_logging_level="debug", reload=False)

    def actualizarFolder(self, folder: str):
        self.folder = folder
        self.folderLabel.content = self.folder

    def agregarDispositivos(self, dispositivo):
        self.listaDispositivos.append(dispositivo)
        self.mostrarPestañas()
