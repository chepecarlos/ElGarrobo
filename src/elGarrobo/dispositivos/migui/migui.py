import logging
import threading

from nicegui import app, ui

from elGarrobo.accionesOOP import accion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.miLibrerias import ConfigurarLogging, SalvarValor, leerData

# librería https://nicegui.io/
# estilo https://tailwindcss.com/
# iconos https://fonts.google.com/icons


logger = ConfigurarLogging(__name__, logging.INFO)


class miGui(dispositivo):
    """
    Interface Web del ElGarrobo
    """

    nombre = "Interfaz Gráfica"
    modulo = "gui"
    tipo = "gui"
    descripcion = "Interfaz web/gráfica (GUI) de ElGarrobo"
    archivoConfiguracion = "gui.md"

    listaDispositivos: list[dispositivo] = None
    "Lista de dispositivos conectados"

    accionEditar: dict
    "Acción medicando o agregando"
    dispositivoEditar: dispositivo
    "dispositivo a modificar la acción"

    colorOscuro: str = "teal-900"
    "Color oscuro de la interfaz"
    colorClaro: str = "teal-300"
    "Color claro de la interfaz"
    colorBotones: str = "teal-500"
    "Color para botones"

    puerto: int = 8080
    "puerto de la interface web"

    folderLabel: ui.label = None
    "Etiqueta del folder del dispositivo actual"
    tipoLabel: ui.label = None
    "Etiqueta del tipo del dispositivo actual"

    def __init__(self, dataConfiguracion: dict) -> None:

        super().__init__(dataConfiguracion)
        self.nombre = dataConfiguracion.get("nombre", "miGui")

        self.puerto = dataConfiguracion.get("puerto", 8080)

        self.folder: str = "?"
        self.listaClasesAcciones: dict = dict()
        self.salvarAcciones: callable = None
        self.ejecutaEvento: callable = None
        self.accionEditar: dict = None
        self.dispositivoEditar: dispositivo = None
        self.opcionesEditar = None
        self.pestañas = None
        self.paneles: ui.tab_panel = None
        self.editorAcción = None

        self.listaDispositivos = list()
        # self.tipo = "GUI"

        # def conectar(self):

        #     super().__init__()

        # def conectar(self) -> None:

        @ui.page("/")
        def paginaAcciones() -> None:
            """Estructura de pagina de acciones"""
            from elGarrobo.accionesOOP.accionListaCheckBox import accionListaCheckBox

            accionListaCheckBox.registrarCliente(ui.context.client)

            with ui.splitter(value=20, limits=(15, 50)) as splitter:
                splitter.classes("w-full")
                with splitter.before:
                    self.mostrarFormulario()
                with splitter.after:
                    self.pestañas = ui.tabs(on_change=self.actualizarCabecera)
                    self.pestañas.classes(f"w-full bg-{self.colorOscuro} text-white")
                    self.paneles = ui.tab_panels(self.pestañas)
                    self.paneles.classes("w-full")
                    self.crearPestañas()
            self.estructura()

        @ui.page("/modulos")
        def paginaModulos():
            from elGarrobo.accionesOOP.accionListaCheckBox import accionListaCheckBox
            from elGarrobo.modulos import cargarModulos

            accionListaCheckBox.registrarCliente(ui.context.client)
            self.mostrarListaActivables("Módulos", "modulos", cargarModulos())
            self.estructura()

        @ui.page("/dispositivos")
        def paginaDispositivos():
            from elGarrobo.accionesOOP.accionListaCheckBox import accionListaCheckBox
            from elGarrobo.dispositivos import cargarDispositivos

            accionListaCheckBox.registrarCliente(ui.context.client)
            self.mostrarListaActivables("Dispositivos", "dispositivos", cargarDispositivos())
            self.estructura()

    def mostrarFormulario(self):
        """Muestra el formulario para agregar o editar acciones"""

        def agregarAcción():
            nombre = self.editorNombre.value
            tecla = self.editorTecla.value
            acción = self.editorAcción.value
            for AtributoAccion in self.listaClasesAcciones.keys():
                objetoClase: accion = self.listaClasesAcciones[AtributoAccion]()
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

            dispositivoDestino = self.dispositivoEditar or self.obtenerDispositivoSeleccionado(nombreDispositivo)
            if dispositivoDestino is None:
                ui.notify(f"No se encontró el dispositivo {nombreDispositivo}")
                return

            if dispositivoDestino.tipo in ["streamdeck", "streamdeckplus", "deck_combinado", "pedal"]:
                try:
                    tecla = int(tecla)
                except ValueError:
                    ui.notify("Error con tecla no numero")
                    return

            if self.botonAgregar.icon == "edit":
                self.accionEditar["nombre"] = nombre
                self.accionEditar["key"] = tecla
                self.accionEditar["accion"] = acción
                self.accionEditar["titulo"] = titulo

                if self.opcionesEditar is not None:
                    try:
                        self.accionEditar["opciones"] = obtenerPropiedades(acción)
                    except Exception as e:
                        return

                ui.notify(f"Editar acción {nombre}")
                logger.info(f"Editar acción {nombre} a {nombreDispositivo}")
            else:
                acciónNueva: dict[str:any] = {"nombre": nombre, "key": tecla, "accion": acción, "titulo": titulo}

                if self.opcionesEditar is not None:
                    try:
                        acciónNueva["opciones"] = obtenerPropiedades(acción)
                    except Exception as e:
                        return

                dispositivoDestino.listaAcciones.append(acciónNueva)
                ui.notify(f"Agregando acción {nombre}")
                logger.info(f"Agregando acción {nombre} a {nombreDispositivo}")

            dispositivoDestino.salvarAcciones()
            self.actualizarPestaña(dispositivoDestino)
            self.limpiarFormulario()

        def obtenerPropiedades(acciónSeleccionada: str) -> dict:
            if self.opcionesEditar is not None:
                opciones = dict()
                for opcionesEditor in self.opcionesEditar.keys():
                    objetoEditor = self.opcionesEditar.get(opcionesEditor)
                    valor = objetoEditor.value
                    accionActual = self.listaClasesAcciones[acciónSeleccionada]()
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
            ancho = "200px"

            # self.editorTitulo.visible = False
            self.editorNombre = ui.input("Nombre").style(f"width: {ancho}").props("clearable")
            self.editorTitulo = ui.input("Titulo").style(f"width: {ancho}").props("clearable")
            self.editorTecla = ui.input("Tecla").style(f"width: {ancho}").props("clearable")

            self.listaNombreAcciones: list[str] = list()
            for clave in self.listaClasesAcciones.keys():
                claseAccion = self.listaClasesAcciones.get(clave)
                nombreAccion = claseAccion().nombre
                self.listaNombreAcciones.append(nombreAccion)

            self.editorAcción = ui.select(options=self.listaNombreAcciones, with_input=True, label="acción", on_change=self.mostrarOpciones).style(f"width: {ancho}")
            self.editorDescripcion = ui.label("").style(f"width: {ancho}").classes("bg-teal-700 p-2 text-white rounded-lg")
            self.editorDescripcion.visible = False
            self.editorPropiedades = ui.column()
            self.editorOpción = ui.textarea(label="Opciones", placeholder="").style(f"width: {ancho}")
            self.editorOpción.visible = False

        with ui.button_group().props("rounded"):
            self.botonAgregar = ui.button(icon="add", color=self.colorOscuro, on_click=agregarAcción)
            ui.button(icon="delete", color=self.colorOscuro, on_click=self.limpiarFormulario)

    def actualizarCabecera(self) -> None:
        """Muestra información del dispositivo rutas de la interfaz web"""
        if self.pestañas is None or self.folderLabel is None:
            return
        pestañaSeleccionada: str = self.pestañas.value
        for dispositivoActual in self.listaDispositivos:
            if dispositivoActual.nombre == pestañaSeleccionada:
                self.folderLabel.text = str(dispositivoActual.folderActual)
                self.folderLabel.update()
                self.tipoLabel.text = str(dispositivoActual.tipo)
                self.tipoLabel.update()
                return

    def mostrarOpciones(self):
        """Muestra las opciones de la acción seleccionada"""
        self.editorDescripcion.text = ""
        self.editorDescripcion.visible = False
        self.editorPropiedades.clear()
        if self.accionEditar:
            claseAccionEditar = self.obtenerAcciónOop(self.accionEditar.get("accion"))
            accionSelecionada = claseAccionEditar().nombre if claseAccionEditar is not None else None
        else:
            accionSelecionada = self.editorAcción.value

        if accionSelecionada is None or accionSelecionada == "":
            return

        logger.info(f"Mostrando opciones para: {accionSelecionada}")

        for acción in self.listaClasesAcciones.keys():
            claseAccion = self.listaClasesAcciones.get(acción)
            acciónTmp: accion = claseAccion()
            # if acción == accionOpciones or acciónTmp.nombre == accionOpciones:
            if acciónTmp.nombre != accionSelecionada:
                continue

            self.editorDescripcion.visible = True
            self.editorDescripcion.text = acciónTmp.descripcion
            with self.editorPropiedades:
                self.opcionesEditar = dict()
                for propiedad in acciónTmp.listaPropiedades:
                    nombre: str = propiedad.nombre
                    etiqueta: str = nombre
                    ejemplo: str = propiedad.ejemplo
                    descripción: str = propiedad.descripcion
                    obligatorio: bool = propiedad.obligatorio
                    if obligatorio:
                        etiqueta = "* " + etiqueta
                    self.opcionesEditar[nombre] = ui.input(label=etiqueta, placeholder=ejemplo)
                    with self.opcionesEditar[nombre]:
                        with ui.button(on_click=lambda d=descripción: ui.notify(d)).props("flat dense"):
                            ui.icon("help", color="teal-300")
            return

        logger.warning(f"No hay opciones para: {accionSelecionada}")

    def limpiarFormulario(self):
        """Limpia el formulario de acciones"""
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
        self.dispositivoEditar = None
        self.opcionesEditar = None

    def crearPestañas(self) -> None:
        """Crea las pestañas de los dispositivos"""
        if self.pestañas is None or self.paneles is None:
            logger.warning("No hay pestañas o paneles para mostrar")
            return

        self.listaDispositivos.sort(key=lambda x: x.nivelOrdenar, reverse=True)

        with self.pestañas:
            for dispositivoActual in self.listaDispositivos:
                nombreDispositivo: str = dispositivoActual.nombre
                dispositivoActual.pestaña = ui.tab(nombreDispositivo)
                dispositivoActual.pestaña.on("click", self.limpiarFormulario)

                with self.paneles:
                    dispositivoActual.panel = ui.tab_panel(dispositivoActual.pestaña)
                    dispositivoActual.panel.classes("h-svh")
                    with dispositivoActual.panel:
                        ui.label(f"Cargando acciones de {nombreDispositivo}...")
                dispositivoActual.funcionActualizarPestaña = self.actualizarPestaña

        self.mostrarPestañas()

    def mostrarPestañas(self) -> None:

        if self.pestañas is None or self.paneles is None:
            logger.warning("No hay pestañas o paneles para mostrar")
            return

        for dispositivoActual in self.listaDispositivos:
            self.actualizarPestaña(dispositivoActual)

        for dispositivoActual in self.listaDispositivos:
            nombreDispositivo = dispositivoActual.nombre
            self.paneles.value = nombreDispositivo
            self.paneles.update()
            self.actualizarCabecera()
            return

    def seleccionarAcción(self, accion: dict, dispositivo: dispositivo = None):
        if dispositivo is not None:
            self.dispositivoEditar = dispositivo
        else:
            self.dispositivoEditar = None

        self.accionEditar = accion
        self.botonAgregar.icon = "edit"
        self.editorNombre.value = accion.get("nombre")

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

        self.editorTitulo.value = accion.get("titulo")

        if opcionesActuales:

            claseAcción = self.listaClasesAcciones.get(self.accionEditar.get("accion"))
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

    def obtenerDispositivoSeleccionado(self, nombreDispositivo: str = None) -> dispositivo:
        """Busca la instancia real del dispositivo por nombre de pestaña

        Args:
            nombreDispositivo (str, optional): Nombre de la pestaña, por defecto la seleccionada
        """
        nombreDispositivo = nombreDispositivo or self.pestañas.value
        for dispositivoActual in self.listaDispositivos:
            if dispositivoActual.nombre == nombreDispositivo:
                return dispositivoActual
        return None

    def mostrarListaActivables(self, titulo: str, archivo: str, listaClases: list) -> None:
        """Lista módulos o dispositivos con un switch para activarlos/desactivarlos

        Args:
            titulo (str): Título de la página
            archivo (str): Archivo de configuración ("modulos" o "dispositivos")
            listaClases (list): Clases con atributos `modulo`, `nombre` y `descripcion`
        """
        configuracion = leerData(archivo) or {}

        def cambiarEstado(clave: str, valor: bool, nombre: str) -> None:
            SalvarValor(archivo, clave, valor)
            ui.notify(f"{nombre} {'activado' if valor else 'desactivado'} - reiniciá elgarrobo para aplicar")

        ui.label(titulo).classes("text-h5 p-4")
        ui.label("Los cambios requieren reiniciar elgarrobo para aplicarse").classes(f"text-caption px-4 text-{self.colorClaro}")
        with ui.column().classes("p-4 gap-2 w-full"):
            for clase in listaClases:
                activo = configuracion.get(clase.modulo, False)
                with ui.row().classes(f"items-center w-full border-b border-{self.colorOscuro} pb-2"):
                    ui.switch(value=activo, on_change=lambda e, c=clase: cambiarEstado(c.modulo, e.value, c.nombre))
                    with ui.column().classes("gap-0"):
                        ui.label(clase.nombre).classes("font-bold")
                        ui.label(clase.descripcion).classes("text-caption")

    def crearDialogoConfirmacion(self, mensaje: str, accionConfirmada) -> ui.dialog:
        """Crea (sin abrir) un dialogo de confirmación para una acción crítica.

        Se crea una sola vez al armar la página: si se crea recién al hacer
        click en el menú, el diálogo no se pinta hasta el siguiente refresco
        porque compite con la animación de cierre del menú.
        """
        with ui.dialog() as dialogo, ui.card():
            ui.label(mensaje)
            with ui.row():
                ui.button("Cancelar", on_click=dialogo.close).props("flat")

                def confirmar():
                    dialogo.close()
                    accionConfirmada()

                ui.button("Confirmar", color="negative", on_click=confirmar).props("flat")
        return dialogo

    def ejecutarAccionSistema(self, comando: str) -> None:
        """Ejecuta una acción registrada por su comando (ej. `salir`, `reiniciar_app`)"""
        claseAccion = self.listaClasesAcciones.get(comando)
        if claseAccion is None:
            ui.notify(f"No se encontró la acción {comando}")
            return
        objetoAccion = claseAccion()
        objetoAccion.configurar()
        objetoAccion.ejecutar()

    def salir(self) -> None:
        """Cierra ElGarrobo"""
        self.ejecutarAccionSistema("salir")

    def reiniciar(self) -> None:
        """Reinicia el proceso de ElGarrobo"""
        self.ejecutarAccionSistema("reiniciar_app")

    def estructura(self):
        """Estructura de la interfaz, cabecera y pie de página"""
        with ui.header(elevated=True) as cabecera:
            cabecera.classes(f"bg-{self.colorOscuro} items-center justify-between")
            cabecera.style("height: 5vh; padding: 1px")
            ui.label("ElGarrobo").classes("text-h5 px-8")
            with ui.row():
                ui.label("Tipo: ")
                self.tipoLabel = ui.label("Cargando...")
                ui.label("Folder: ")
                self.folderLabel = ui.label("Cargando...")
            dialogoReiniciar = self.crearDialogoConfirmacion("¿Reiniciar ElGarrobo?", self.reiniciar)
            dialogoSalir = self.crearDialogoConfirmacion("¿Cerrar ElGarrobo?", self.salir)
            with ui.button(icon="menu").props("flat color=white").classes("px-8"):
                with ui.menu():
                    ui.menu_item("Acciones", on_click=lambda: ui.navigate.to("/"))
                    ui.menu_item("Módulos", on_click=lambda: ui.navigate.to("/modulos"))
                    ui.menu_item("Dispositivos", on_click=lambda: ui.navigate.to("/dispositivos"))
                    ui.separator()
                    ui.menu_item("Reiniciar", on_click=dialogoReiniciar.open)
                    ui.menu_item("Salir", on_click=dialogoSalir.open)

        with ui.footer().classes(f"bg-{self.colorOscuro}").style("height: 5vh; padding: 1px"):
            with ui.row().classes("w-full").style("padding: 0 10px"):
                ui.label("Creado por ChepeCarlos")
                ui.space()
                ui.link("Youtube", "https://www.youtube.com/@chepecarlo")
                ui.link("Tiktok", "https://www.tiktok.com/@chepecarlo")

    def seConectorGUI(self, client=None):
        """
        Inicia la interface web.
        """
        from elGarrobo.accionesOOP.accionListaCheckBox import accionListaCheckBox

        if client is not None:
            accionListaCheckBox.registrarCliente(client)
            logger.info(f"Conectando NiceGUI - cliente {client.id}")
        else:
            logger.info("Conectando NiceGUI")

    def seDesconectoGUI(self, client=None):
        """
        Desconecta la interface web.
        """
        if client is not None:
            logger.info(f"Desconectando NiceGUI - cliente {client.id}")
        else:
            logger.info("Desconectando NiceGUI")
        # app.shutdown()

    def conectar(self):

        logger.info("Iniciando NiceGUI")

        app.on_connect(self.seConectorGUI)
        app.on_disconnect(self.seDesconectoGUI)

        self.HiloGui = threading.Thread(name="Gui-" + self.nombre, target=self.funciónHilo)
        self.HiloGui.start()

    def funciónHilo(self):
        logger.info("Iniciando GUI - Hilo")
        try:
            ui.run(
                title="ElGarrobo",
                port=self.puerto,
                reload=False,
                show=False,
                dark=True,
                language="es",
                uvicorn_logging_level="warning",
                favicon="🦎",
            )
        except Exception as error:
            logger.error(f"GUI[Error] No se puedo iniciar GUI - {error}")

    def desconectar(self) -> None:
        logger.info("Saliendo de NiceGUI")
        app.shutdown()

    def agregarAcciones(self, listaClasesAcciones: list):
        for accion in listaClasesAcciones:
            self.listaClasesAcciones.append(accion)
        self.listaClasesAcciones.sort()
        if self.editorAcción is not None:
            self.editorAcción.options = self.listaClasesAcciones
            self.editorAcción.update()

    def actualizarAcciones(self, nombreDispositivo: str, acciones: list, folder: str):
        self.mostrarPestañas()

    def obtenerAcciónOop(self, comandoAcción: str) -> accion:
        """Obtiene la clase de accion

        Args:
            comandoAcción (str) : Comando que representa la accion
        Returns:
            accion: La clase de la accion
        """
        if comandoAcción in self.listaClasesAcciones:
            return self.listaClasesAcciones[comandoAcción]
        return None

    def obtenerRutaImagen(self, Imagen: str, folder: str):
        if Imagen is None:
            return
        pass

    def actualizarPestaña(self, dispositivo: dispositivo) -> None:
        """Actualiza las acciones de la pestaña del dispositivo

        Args:
            dispositivo (dispositivo): dispositivo a actualizar la pestaña
        """
        nombre = dispositivo.nombre
        tipo = dispositivo.tipo
        input = dispositivo.dispositivo
        folder = dispositivo.folderActual
        # clase = dispositivo.clase

        if self.paneles is None:
            logger.warning("No hay paneles")
            return

        if dispositivo.panel is None:
            logger.warning(f"dispositivo {nombre} sin panel")
            return

        with self.paneles:
            dispositivo.panel.clear()
            with dispositivo.panel:
                acciones = dispositivo.listaAcciones

                with ui.scroll_area() as areaScroll:
                    areaScroll.classes("h-96 border border-2 border-teal-600h")
                    areaScroll.style("height: 75vh")

                    if acciones is None:
                        ui.label("No acciones")
                        return

                    self.dibujarAcciones(acciones, dispositivo)

            self.actualizarCabecera()

        if hasattr(dispositivo, "actualizarIconos"):
            dispositivo.actualizarIconos()

    def dibujarAcciones(self, listaAcciones: list[dict], dispositivo: dispositivo) -> None:
        """Dibuja las acciones de los dispositivos en la interfaz web

        Args:
            listaAcciones (list[dict]): Lista de acciones a dibujar
        """

        with ui.row().classes("content p-2"):
            ui.label("Nombre").style("font-weight: bold; width: 100px")
            ui.label("Titulo").style("font-weight: bold; width: 100px")
            # ui.label("Imagen").style("font-weight: bold; width: 150px")
            ui.label("Tecla").style("font-weight: bold; width: 100px")
            ui.label("Acción").style("font-weight: bold; width: 125px")
            ui.label("Opciones").style("font-weight: bold; width: 180px")

        for acciónActual in listaAcciones:
            nombreAcción = acciónActual.get("nombre")
            teclaAcción = acciónActual.get("key")
            acciónAcción = acciónActual.get("accion")
            tituloAcción = acciónActual.get("titulo")
            imagenAcción = acciónActual.get("imagen")

            with ui.row().classes("content p-2 border-2 border-teal-600"):
                ui.label(nombreAcción).style("width: 100px")
                ui.label(tituloAcción).style("width: 100px")
                # if tipo == "steamdeck":
                # ui.image(imagenAcción)

                # imagenAcción = self.obtenerRutaImagen(imagenAcción, folder)
                # if imagenAcción is not None:
                #     # ui.label(imagenAcción).style("width: 150px")
                #     pass
                # else:
                #     pass
                # ColorFondo = "black"
                # image: Image = Image.new("RGB", [100, 100], color=ColorFondo)
                # ObtenerImagen(image, acciónActual, folder)

                # imagen = ui.image(image).classes("w-12").style("width: 150px")
                # imagen.on("click", lambda a=acciónActual: self.seleccionarAcción(a))
                # ui.label("").style("width: 150px")

                ui.label(teclaAcción).style("width: 100px")

                claseAcción = self.obtenerAcciónOop(acciónAcción)
                if claseAcción is not None:
                    objetoAcción = claseAcción()
                    nombreClase = objetoAcción.nombre
                    ui.label(f"{nombreClase}").style("width: 125px")
                else:
                    ui.label(f"{acciónAcción}-vieja").style("width: 125px")
                    # TODO: montar función viejas

                with ui.button_group().props("rounded"):
                    ui.button(icon="play_arrow", color="teal-500", on_click=lambda a=acciónActual: self.buscarAccion(a, self.estadoTecla.PRESIONADA))
                    ui.button(icon="edit", color="teal-500", on_click=lambda a=acciónActual: self.seleccionarAcción(a, dispositivo))
                    ui.button(icon="delete", color="teal-500", on_click=lambda a=acciónActual, d=dispositivo: self.borrarAcción(a, d))

    def buscarAccion(self, acción: dict, estado):
        logger.info(f"Evento[{acción.get('nombre')}] {self.nombre}[{acción.get('key')}-{estado.name}]")
        self.ejecutarAcción(acción)

    def borrarAcción(self, accion, dispositivo: dispositivo):
        dispositivo.listaAcciones.remove(accion)
        dispositivo.salvarAcciones()
        self.actualizarPestaña(dispositivo)

    def actualizarIconos(self):
        logger.info("Dibujando GUI")

        # self.editorAcción.update()

        # su
        pass

    def actualizar(self):

        logger.info("Actualizando GUI")

        super().actualizar()
