import copy
import logging
import threading

import yaml
from nicegui import app, ui

from elGarrobo.accionesOOP import accion
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.dispositivos.dataAccion import dataAccion
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
        self.editoresData: dict = {}
        self.ordenCampo: str = "key"
        self.dispositivosEnLista: set[str] = set()
        self.dispositivoFolder = None
        "Dispositivo cuyas propiedades del folder se están editando"
        "Dispositivos con distribución física que el usuario cambió a vista de lista"
        self.ordenInverso: bool = False
        self.teclaIntercambio: dict = {}
        "Dispositivos en modo intercambiar → primera tecla seleccionada (None si aún no hay)"

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
            # Las etiquetas de la cabecera se crean en estructura(), después de las pestañas
            self.actualizarCabecera()

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

    @staticmethod
    def teclaRepetida(listaAcciones: list[dict], tecla, ignorar: dict = None) -> dict:
        """Devuelve la acción que ya usa la tecla (sin contar ignorar), o None"""
        for acción in listaAcciones:
            if acción is not ignorar and str(acción.get("key")) == str(tecla):
                return acción
        return None

    @staticmethod
    def ordenTecla(acción: dict) -> tuple:
        """Números primero (streamdeck/pedal), luego texto (teclados), sin comparar int con str"""
        tecla = acción.get("key")
        return (0, tecla, "") if isinstance(tecla, int) else (1, 0, str(tecla))

    @staticmethod
    def ordenarAcciones(listaAcciones: list[dict], campo: str, inverso: bool = False) -> list[dict]:
        """Copia ordenada de las acciones por "nombre", "titulo", "key" o "accion", sin tocar la lista guardada"""
        if campo == "key":
            orden = miGui.ordenTecla
        else:
            orden = lambda acción: str(acción.get(campo) or "").lower()
        return sorted(listaAcciones, key=orden, reverse=inverso)

    def cambiarOrden(self, campo: str, dispositivo: dispositivo) -> None:
        """Ordena por campo; si ya estaba ordenado por ese campo invierte el sentido"""
        self.ordenInverso = not self.ordenInverso if self.ordenCampo == campo else False
        self.ordenCampo = campo
        self.actualizarPestaña(dispositivo)

    def mostrarFormulario(self):
        """Muestra el formulario para agregar o editar acciones"""

        def agregarAcción():
            # Los vacíos son None para no guardar claves vacías en el .md
            valores = {atributo: None if editor.value in ("", None) else editor.value for atributo, editor in self.editoresData.items()}
            nombre = valores["nombre"]
            tecla = valores["key"]
            acción = self.editorAcción.value
            acción = self.comandoAcción(acción) or acción
            nombreDispositivo = self.pestañas.value

            if not nombreDispositivo:
                ui.notify(f"Selecciones un dispositivo")
                return
            for propiedad in dataAccion.propiedadesGui():
                if propiedad.obligatorio and not valores[propiedad.atributo]:
                    ui.notify(f"Ingrese {propiedad.nombre}")
                    return
            if not acción:
                ui.notify(f"Seleccione una acción")
                return

            dispositivoDestino = self.dispositivoEditar or self.obtenerDispositivoSeleccionado(nombreDispositivo)
            if dispositivoDestino is None:
                ui.notify(f"No se encontró el dispositivo {nombreDispositivo}")
                return

            if dispositivoDestino.tipo in ["streamdeck", "streamdeckplus", "deck_combinado", "pedal"]:
                try:
                    tecla = valores["key"] = int(tecla)
                except ValueError:
                    ui.notify("Error con tecla no numero")
                    return

            editando = self.botonAgregar.icon == "edit"
            repetida = self.teclaRepetida(dispositivoDestino.listaAcciones, tecla, self.accionEditar if editando else None)
            if repetida is not None:
                ui.notify(f"La tecla {tecla} ya está usada por '{repetida.get('nombre')}', cámbiela", type="warning")
                return

            if editando:
                for atributo, valor in valores.items():
                    self.accionEditar[atributo] = valor
                self.accionEditar["accion"] = acción
                self.aplicarApariencia(self.accionEditar)

                if self.opcionesEditar is not None:
                    try:
                        self.accionEditar["opciones"] = obtenerPropiedades(acción)
                    except Exception as e:
                        return

                ui.notify(f"Editar acción {nombre}")
                logger.info(f"Editar acción {nombre} a {nombreDispositivo}")
            else:
                acciónNueva: dict[str:any] = {**valores, "accion": acción}

                if self.opcionesEditar is not None:
                    try:
                        acciónNueva["opciones"] = obtenerPropiedades(acción)
                    except Exception as e:
                        return

                acciónNueva = dataAccion.desdeDict(acciónNueva)
                self.aplicarApariencia(acciónNueva)
                dispositivoDestino.listaAcciones.append(acciónNueva)
                ui.notify(f"Agregando acción {nombre}")
                logger.info(f"Agregando acción {nombre} a {nombreDispositivo}")

            dispositivoDestino.listaAcciones.sort(key=self.ordenTecla)
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

        with ui.scroll_area().classes("w-full").style("height: 75vh"):

            # Campos de dataAccion marcados con gui, la clave del dict es la clave en el .md
            self.editoresData = {propiedad.atributo: self.crearEditor(propiedad, f"editor-{propiedad.atributo}").props("clearable") for propiedad in dataAccion.propiedadesGui()}

            # Propiedades del folder: valores por defecto de los botones del folder actual
            with ui.dialog() as self.dialogoFolder, ui.card():
                ui.label("Apariencia del folder").classes("text-lg")
                ui.label("Valores por defecto de los botones de este folder").classes("text-xs")
                self.editorFolderFondo = ui.color_input("Fondo", preview=True).classes("w-64").mark("editor-folder-fondo")
                self.editorFolderTamaño = ui.number("Tamaño máximo del título", min=1, precision=0).classes("w-64").mark("editor-folder-tamanno")
                ui.button("Guardar", on_click=self.guardarPropiedadesFolder).mark("botonGuardarFolder")

            # Se llena al abrir con las distribuciones disponibles
            with ui.dialog() as self.dialogoDistribucion, ui.card():
                self.listaDistribuciones = ui.column()

            # Apariencia del botón en un diálogo aparte para no llenar el formulario
            with ui.dialog() as self.dialogoBoton, ui.card():
                ui.label("Apariencia del botón").classes("text-lg")
                with ui.row().classes("items-start no-wrap"):
                    with ui.column().classes("w-64"):
                        self.editorTitulo = ui.input("Titulo", on_change=self.actualizarVistaPrevia).classes("w-full").props("clearable").mark("editor-titulo")
                        self.editorFondo = ui.color_input("Fondo", preview=True, on_change=self.actualizarVistaPrevia).classes("w-full").mark("editor-fondo")
                    self.vistaPrevia = ui.image().classes("w-24 h-24 rounded").mark("vistaPrevia")
                ui.button("Listo", on_click=self.dialogoBoton.close).mark("botonListoBoton")
            ui.button("Editar apariencia", icon="palette", color=self.colorOscuro, on_click=self.abrirEditorApariencia).classes("w-full").mark("botonEditarBoton")

            self.listaNombreAcciones: list[str] = list()
            for clave in self.listaClasesAcciones.keys():
                claseAccion = self.listaClasesAcciones.get(clave)
                nombreAccion = claseAccion().nombre
                self.listaNombreAcciones.append(nombreAccion)

            self.editorAcción = ui.select(options=self.listaNombreAcciones, with_input=True, label="acción", on_change=self.mostrarOpciones).classes("w-full").mark("editorAcción")
            self.editorDescripcion = ui.label("").classes("w-full bg-teal-700 p-2 text-white rounded-lg")
            self.editorDescripcion.visible = False
            self.editorPropiedades = ui.column().classes("w-full")
            self.editorOpción = ui.textarea(label="Opciones (solo lectura, se conservan al guardar)").classes("w-full").props("readonly").mark("editorOpción")
            self.editorOpción.visible = False

        with ui.button_group().props("rounded"):
            self.botonAgregar = ui.button(icon="add", color=self.colorOscuro, on_click=agregarAcción).mark("botonAgregar")
            self.botonAgregar.tooltip("Guardar acción")
            # Solo se ven al editar una acción guardada
            self.botonEjecutar = ui.button(icon="play_arrow", color=self.colorOscuro, on_click=lambda: self.buscarAccion(self.accionEditar, self.estadoTecla.PRESIONADA)).mark("botonEjecutar")
            self.botonEjecutar.tooltip("Ejecutar acción guardada")
            ui.button(icon="clear_all", color=self.colorOscuro, on_click=self.limpiarFormulario).mark("botonLimpiar").tooltip("Limpiar editor")
            self.botonBorrar = ui.button(icon="delete", color=self.colorOscuro, on_click=self.borrarAcciónEditada).mark("botonBorrar")
            self.botonBorrar.tooltip("Borrar acción")
            self.botonEjecutar.visible = self.botonBorrar.visible = False

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
        # Guarda los valores para pasarlos a las propiedades con el mismo nombre de la nueva acción
        valoresAnteriores = {nombre: editor.value for nombre, editor in (self.opcionesEditar or {}).items()}
        self.editorPropiedades.clear()
        accionSeleccionada = self.editorAcción.value

        if accionSeleccionada is None or accionSeleccionada == "":
            return

        logger.info(f"Mostrando opciones para: {accionSeleccionada}")

        for acción in self.listaClasesAcciones.keys():
            claseAccion = self.listaClasesAcciones.get(acción)
            acciónTmp: accion = claseAccion()
            # if acción == accionOpciones or acciónTmp.nombre == accionOpciones:
            if acciónTmp.nombre != accionSeleccionada:
                continue

            self.editorDescripcion.visible = True
            self.editorDescripcion.text = acciónTmp.descripcion
            with self.editorPropiedades:
                self.opcionesEditar = dict()
                for propiedad in acciónTmp.listaPropiedades:
                    nombre: str = propiedad.nombre
                    editor = self.crearEditor(propiedad, f"opción-{nombre}")
                    if valoresAnteriores.get(nombre):
                        editor.value = valoresAnteriores[nombre]
                    self.opcionesEditar[nombre] = editor
            return

        logger.warning(f"No hay opciones para: {accionSeleccionada}")

    @staticmethod
    def crearEditor(propiedad: propiedadAccion, marca: str) -> ui.input:
        """Crea el input de una propiedad: * si es obligatoria, ejemplo, ayuda y textarea si es multilinea"""
        etiqueta = f"* {propiedad.nombre}" if propiedad.obligatorio else propiedad.nombre
        crearInput = ui.textarea if propiedad.multilinea else ui.input
        editor = crearInput(label=etiqueta, placeholder=propiedad.ejemplo).classes("w-full").mark(marca)
        if propiedad.descripcion:
            with editor:
                with ui.button(on_click=lambda d=propiedad.descripcion: ui.notify(d)).props("flat dense"):
                    ui.icon("help", color="teal-300")
        return editor

    def comandoAcción(self, nombreAcción: str) -> str | None:
        """Comando de la acción a partir del nombre que muestra el selector"""
        for claseAcción in self.listaClasesAcciones.values():
            objetoClase: accion = claseAcción()
            if objetoClase.nombre == nombreAcción:
                return objetoClase.comando
        return None

    def abrirEditorApariencia(self) -> None:
        self.actualizarVistaPrevia()
        self.dialogoBoton.open()

    def actualizarVistaPrevia(self, *_) -> None:
        """Dibuja el botón con lo que hay en el formulario, sin guardar"""
        dispositivoActual = self.dispositivoEditar or (self.obtenerDispositivoSeleccionado() if self.pestañas else None)
        if dispositivoActual is None:
            return

        # Copia profunda: imagen_opciones es un dict y aplicarApariencia lo modifica, no debe tocar la acción guardada
        acción = copy.deepcopy(self.accionEditar) if self.accionEditar else dataAccion()
        acción.accion = self.comandoAcción(self.editorAcción.value) or acción.accion
        self.aplicarApariencia(acción)
        try:
            imagen = dispositivoActual.dibujo().dibujar(acción, dispositivoActual.tamañoBoton(), conGif=True)
        except Exception as error:
            # Ej: color a medio escribir, se deja la vista previa anterior
            logger.debug(f"Vista previa[Error] {error}")
            return
        self.vistaPrevia.set_source(imagen)

    def aplicarApariencia(self, acción: dataAccion) -> None:
        """Pasa a la acción el título y fondo del editor del botón"""
        acción.titulo = self.editorTitulo.value or None
        acción.fondo = self.editorFondo.value or None

    def limpiarFormulario(self):
        """Limpia el formulario de acciones"""
        self.botonAgregar.icon = "add"
        self.botonEjecutar.visible = self.botonBorrar.visible = False
        for editor in self.editoresData.values():
            editor.value = ""
        self.editorTitulo.value = ""
        self.editorFondo.value = ""
        self.editorAcción.value = ""
        self.editorOpción.value = ""
        self.editorOpción.visible = False
        self.editorAcción.set_options(self.listaNombreAcciones)
        self.editorDescripcion.text = ""
        self.editorDescripcion.visible = False
        self.editorPropiedades.clear()
        self.accionEditar = None
        self.dispositivoEditar = None
        self.opcionesEditar = None

    def borrarAcciónEditada(self) -> None:
        """Borra la acción que está en el editor y lo limpia"""
        acción, dispositivo = self.accionEditar, self.dispositivoEditar
        self.limpiarFormulario()
        self.borrarAcción(acción, dispositivo)
        ui.notify(f"Acción {acción.get('nombre')} borrada")

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
        self.botonEjecutar.visible = self.botonBorrar.visible = True
        for atributo, editor in self.editoresData.items():
            editor.value = accion.get(atributo)
        self.editorTitulo.value = accion.titulo or ""
        self.editorFondo.value = accion.fondo or ""

        # Sin esto mostrarOpciones pasaría los valores de la acción editada antes
        self.opcionesEditar = None
        claseAcción = self.obtenerAcciónOop(accion.get("accion"))
        if claseAcción is None:
            # Acción sin clase OOP (ej. macro): se agrega al selector para no perderla al guardar
            comando = accion.get("accion")
            self.editorAcción.set_options(self.listaNombreAcciones + [comando], value=comando)
        else:
            objetoClase = claseAcción()
            self.editorAcción.value = objetoClase.nombre
        self.mostrarOpciones()
        opcionesActuales = accion.get("opciones")
        self.editorOpción.visible = False

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
                # Sin editor para estas opciones (ej. pasos de una macro): se muestran y se guardan sin cambios
                self.editorOpción.visible = True
                self.editorOpción.value = yaml.safe_dump(opcionesActuales, allow_unicode=True, sort_keys=False)

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
                    ui.menu_item("Acciones", on_click=lambda: ui.navigate.to("/")).mark("menu-Acciones")
                    ui.menu_item("Módulos", on_click=lambda: ui.navigate.to("/modulos")).mark("menu-Módulos")
                    ui.menu_item("Dispositivos", on_click=lambda: ui.navigate.to("/dispositivos")).mark("menu-Dispositivos")
                    ui.separator()
                    ui.menu_item("Reiniciar", on_click=dialogoReiniciar.open).mark("menu-Reiniciar")
                    ui.menu_item("Salir", on_click=dialogoSalir.open).mark("menu-Salir")

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
                cuadricula = dispositivo.gruposBotones() is not None or dispositivo.distribucionTeclas() is not None
                if not cuadricula and hasattr(dispositivo, "cambiarDistribucion"):
                    # Teclado sin distribución: único camino para elegir una
                    self.botonDistribucion(dispositivo)
                if cuadricula:
                    ui.toggle(
                        {False: "Cuadrícula", True: "Lista"},
                        value=nombre in self.dispositivosEnLista,
                        on_change=lambda e, d=dispositivo: self.cambiarVista(d, e.value),
                    ).mark(f"vista-{nombre}")

                with ui.scroll_area() as areaScroll:
                    areaScroll.classes("w-full border-2 border-teal-600")
                    # Alto disponible: 100vh - cabecera (5vh) - pie (5vh) - pestañas (48px) - padding del panel (32px) - interruptor (40px)
                    areaScroll.style(f"height: calc(90vh - {120 if cuadricula else 80}px)")

                    if acciones is None:
                        ui.label("No acciones")
                        return

                    if cuadricula and nombre not in self.dispositivosEnLista:
                        self.dibujarCuadricula(acciones, dispositivo)
                    else:
                        self.dibujarAcciones(acciones, dispositivo)

            self.actualizarCabecera()

        if hasattr(dispositivo, "actualizarIconos"):
            dispositivo.actualizarIconos()

    def cambiarVista(self, dispositivo: dispositivo, enLista: bool) -> None:
        if enLista:
            self.dispositivosEnLista.add(dispositivo.nombre)
        else:
            self.dispositivosEnLista.discard(dispositivo.nombre)
        self.actualizarPestaña(dispositivo)

    def dibujarCuadricula(self, listaAcciones: list, dispositivo: dispositivo) -> None:
        """Dibuja la página actual del dispositivo como sus botones físicos, con la vista previa de cada uno

        Args:
            listaAcciones (list): Lista de acciones del dispositivo
            dispositivo (dispositivo): dispositivo con gruposBotones() o distribucionTeclas()
        """
        grupos = dispositivo.gruposBotones() or []
        distribucion = dispositivo.distribucionTeclas()
        accionesPorTecla = {str(acción.get("key")): acción for acción in listaAcciones}
        nombre = dispositivo.nombre

        with ui.row().classes("items-center p-2 w-full"):
            subir = ui.button(icon="arrow_upward", color="teal-500", on_click=lambda: self.subirFolder(dispositivo)).mark(f"subirFolder-{nombre}")
            subir.tooltip("Subir al folder anterior")
            subir.set_enabled(not dispositivo.enFolderRaiz())
            if hasattr(dispositivo, "siguientePagina") and grupos:
                anterior = ui.button(icon="chevron_left", color="teal-500", on_click=lambda: self.cambiarPagina(dispositivo, dispositivo.anteriorPagina)).mark(f"paginaAnterior-{nombre}")
                anterior.set_enabled(dispositivo.puedeAnteriorPagina())
                ui.label(f"Página {dispositivo.paginaActual()}").mark(f"pagina-{nombre}")
                siguiente = ui.button(icon="chevron_right", color="teal-500", on_click=lambda: self.cambiarPagina(dispositivo, dispositivo.siguientePagina)).mark(f"paginaSiguiente-{nombre}")
                siguiente.set_enabled(dispositivo.puedeSiguientePagina())
            intercambiando = nombre in self.teclaIntercambio
            seleccionada = self.teclaIntercambio.get(nombre)
            ui.button("Intercambiar", icon="swap_horiz", color="orange-8" if intercambiando else "teal-500", on_click=lambda: self.cambiarModoIntercambio(dispositivo)).classes("ml-auto").mark(f"intercambiar-{nombre}")
            ui.button("Apariencia folder", icon="folder_special", color="teal-500", on_click=lambda: self.abrirPropiedadesFolder(dispositivo)).mark(f"propiedadesFolder-{nombre}")
            if hasattr(dispositivo, "cambiarDistribucion"):
                self.botonDistribucion(dispositivo)

        def alClick(tecla, acción):
            if intercambiando:
                return lambda: self.seleccionarIntercambio(dispositivo, tecla)
            if acción is not None:
                return lambda: self.seleccionarAcción(acción, dispositivo)
            return lambda: self.nuevaAcciónTecla(dispositivo, tecla)

        def marcar(boton, tecla) -> None:
            if intercambiando and tecla == seleccionada:
                boton.classes("ring-4 ring-orange-500")
            boton.mark(f"tecla-{nombre}-{tecla}")

        if distribucion:
            # Teclado: botones con posición libre en unidades de tecla, sin vista previa porque no tiene pantalla
            unidad = 56
            ancho, alto = self.medidaDistribucion(distribucion)
            with ui.element("div").classes("relative m-2").style(f"width: {ancho * unidad}px; height: {alto * unidad}px"):
                for teclaFisica in distribucion:
                    tecla = teclaFisica["key"]
                    acción = accionesPorTecla.get(tecla)
                    etiqueta = teclaFisica.get("etiqueta") or tecla.removeprefix("KEY_")
                    x, y = teclaFisica.get("x", 0), teclaFisica.get("y", 0)
                    w, h = teclaFisica.get("w", 1), teclaFisica.get("h", 1)
                    boton = ui.button(acción.get("nombre") if acción else etiqueta, color="teal-600" if acción else "grey-8", on_click=alClick(tecla, acción))
                    boton.props("dense no-caps").classes("absolute text-xs leading-tight overflow-hidden")
                    boton.style(f"left: {x * unidad}px; top: {y * unidad}px; width: {w * unidad - 4}px; height: {h * unidad - 4}px")
                    boton.tooltip(f"{etiqueta} ({tecla})" + (f": {acción.get('nombre')}" if acción else ""))
                    marcar(boton, tecla)

            # Acciones en teclas que no están dibujadas (capa Fn, teclas de otro modelo) para que no queden escondidas
            dibujadas = {t["key"] for t in distribucion} | {"propiedad_folder"}
            otras = [tecla for tecla in accionesPorTecla if tecla not in dibujadas]
            if otras:
                ui.label("Otras teclas").classes("font-bold px-2")
                with ui.row().classes("gap-1 px-2"):
                    for tecla in otras:
                        acción = accionesPorTecla[tecla]
                        boton = ui.button(acción.get("nombre"), color="teal-600", on_click=alClick(tecla, acción)).props("dense no-caps")
                        boton.classes("text-xs").tooltip(tecla)
                        marcar(boton, tecla)

        with ui.row().classes("items-start gap-8 p-2"):
            for grupo in grupos:
                dibujante = grupo.dibujante
                dibujo = dibujante.dibujo()
                tamaño = dibujante.tamañoBoton()
                # El aparato ya está rotado frente al usuario, el ícono se muestra derecho
                rotarAparato = getattr(dibujante, "rotar", 0)

                with ui.column().classes("items-center"):
                    if len(grupos) > 1:
                        ui.label(grupo.nombre).classes("font-bold")
                    with ui.grid(columns=grupo.columnas).classes("gap-2"):
                        for indice in range(grupo.filas * grupo.columnas):
                            tecla = grupo.primeraTecla + indice
                            acción = accionesPorTecla.get(str(tecla))
                            imagen = None
                            if acción is not None:
                                try:
                                    imagen = dibujo.dibujar(acción, tamaño, conGif=True, compensarRotar=rotarAparato)
                                except Exception as error:
                                    logger.warning(f"Vista previa[Error] {nombre}[{tecla}] {error}")

                            with ui.column().classes("items-center gap-1"):
                                if imagen is not None:
                                    boton = ui.image(imagen).classes("w-24 h-24 rounded cursor-pointer")
                                    boton.on("click", alClick(tecla, acción))
                                else:
                                    boton = ui.button(icon="add", color="grey-8", on_click=alClick(tecla, acción)).classes("w-24 h-24")
                                marcar(boton, tecla)
                                ui.label(f"{tecla}: {acción.get('nombre')}" if acción is not None else str(tecla)).classes("text-xs")

    @staticmethod
    def medidaDistribucion(distribucion: list[dict]) -> tuple[float, float]:
        """Ancho y alto del teclado en unidades de tecla"""
        ancho = max(t.get("x", 0) + t.get("w", 1) for t in distribucion)
        alto = max(t.get("y", 0) + t.get("h", 1) for t in distribucion)
        return ancho, alto

    def botonDistribucion(self, dispositivo: dispositivo) -> None:
        ui.button("Distribución", icon="keyboard", color="teal-500", on_click=lambda: self.abrirDistribuciones(dispositivo)).mark(f"distribucion-{dispositivo.nombre}")

    def abrirDistribuciones(self, dispositivo: dispositivo) -> None:
        """Muestra las distribuciones disponibles con una miniatura; al elegir una se guarda en teclados.md"""
        from elGarrobo.dispositivos.miteclado.mi_teclado_macro import cargarDistribucion, distribucionesDisponibles, folderDistribucionesUsuario

        def elegir(nombreDistribucion: str | None) -> None:
            dispositivo.cambiarDistribucion(nombreDistribucion)
            self.dialogoDistribucion.close()
            ui.notify(f"Distribución de {dispositivo.nombre}: {nombreDistribucion or 'ninguna'}")
            self.actualizarPestaña(dispositivo)

        unidad = 10
        self.listaDistribuciones.clear()
        with self.listaDistribuciones:
            ui.label(f"Distribución de {dispositivo.nombre}").classes("text-lg")
            ui.label(f"Agrega las tuyas (JSON de keyboard-layout-editor.com) en {folderDistribucionesUsuario()}").classes("text-xs")
            for nombreDistribucion in [None, *distribucionesDisponibles()]:
                actual = nombreDistribucion == dispositivo.distribucion
                with ui.card().classes(f"w-full cursor-pointer {'border-2 border-orange-500' if actual else ''}") as tarjeta:
                    tarjeta.on("click", lambda n=nombreDistribucion: elegir(n))
                    tarjeta.mark(f"opcionDistribucion-{nombreDistribucion}")
                    ui.label(nombreDistribucion or "Ninguna (ver como lista)").classes("font-bold")
                    distribucion = cargarDistribucion(nombreDistribucion) if nombreDistribucion else None
                    if distribucion:
                        ancho, alto = self.medidaDistribucion(distribucion)
                        with ui.element("div").classes("relative").style(f"width: {ancho * unidad}px; height: {alto * unidad}px"):
                            for t in distribucion:
                                estilo = f"left: {t.get('x', 0) * unidad}px; top: {t.get('y', 0) * unidad}px; width: {t.get('w', 1) * unidad - 1}px; height: {t.get('h', 1) * unidad - 1}px"
                                ui.element("div").classes("absolute bg-grey-6 rounded-sm").style(estilo)
        self.dialogoDistribucion.open()

    def cambiarModoIntercambio(self, dispositivo: dispositivo) -> None:
        """Activa o desactiva el modo intercambiar teclas en la cuadrícula del dispositivo"""
        if self.teclaIntercambio.pop(dispositivo.nombre, False) is False:
            self.teclaIntercambio[dispositivo.nombre] = None
        self.actualizarPestaña(dispositivo)

    def seleccionarIntercambio(self, dispositivo: dispositivo, tecla: int) -> None:
        """Primer click marca la tecla, el segundo intercambia ambas; si una está vacía la acción se mueve ahí"""
        primera = self.teclaIntercambio.get(dispositivo.nombre)
        self.teclaIntercambio[dispositivo.nombre] = tecla if primera is None else None
        if primera is not None and primera != tecla:
            porTecla = {str(acción.get("key")): acción for acción in dispositivo.listaAcciones}
            acciónA, acciónB = porTecla.get(str(primera)), porTecla.get(str(tecla))
            if acciónA is not None:
                acciónA.key = tecla
            if acciónB is not None:
                acciónB.key = primera
            if acciónA is not None or acciónB is not None:
                dispositivo.listaAcciones.sort(key=self.ordenTecla)
                dispositivo.salvarAcciones()
                dispositivo.actualizar()
        self.actualizarPestaña(dispositivo)

    def abrirPropiedadesFolder(self, dispositivo: dispositivo) -> None:
        """Carga en el diálogo la propiedad_folder del folder actual del dispositivo"""
        self.dispositivoFolder = dispositivo
        propiedad = dispositivo.propiedadFolder
        self.editorFolderFondo.value = (propiedad.fondo if propiedad else None) or ""
        self.editorFolderTamaño.value = (propiedad.tituloOpciones.get("tamanno_maximo") if propiedad else None)
        self.dialogoFolder.open()

    def guardarPropiedadesFolder(self) -> None:
        """Guarda la propiedad_folder; la crea si no existe y la quita si queda vacía"""
        dispositivo = self.dispositivoFolder
        propiedad = dispositivo.propiedadFolder
        if propiedad is None:
            propiedad = dataAccion(key="propiedad_folder")
            dispositivo.listaAcciones.append(propiedad)

        propiedad.fondo = self.editorFolderFondo.value or None
        tamaño = self.editorFolderTamaño.value
        if tamaño:
            propiedad.tituloOpciones["tamanno_maximo"] = int(tamaño)
        else:
            propiedad.tituloOpciones.pop("tamanno_maximo", None)

        if propiedad.aDict() == {"key": "propiedad_folder"}:
            dispositivo.listaAcciones.remove(propiedad)

        dispositivo.salvarAcciones()
        self.dialogoFolder.close()
        ui.notify(f"Apariencia del folder guardada en {dispositivo.nombre}")
        self.actualizarPestaña(dispositivo)

    def subirFolder(self, dispositivo: dispositivo) -> None:
        """Carga el folder anterior en el dispositivo; avisa a la GUI al cargar"""
        dispositivo.regresarFolderActual()
        dispositivo.actualizar()

    def cambiarPagina(self, dispositivo: dispositivo, cambiar) -> None:
        """Cambia la página del dispositivo físico; el dispositivo avisa a la GUI para redibujar la pestaña"""
        cambiar()
        dispositivo.actualizar()

    def nuevaAcciónTecla(self, dispositivo: dispositivo, tecla: int) -> None:
        """Prepara el formulario para agregar una acción en una tecla vacía de la cuadrícula"""
        self.limpiarFormulario()
        self.dispositivoEditar = dispositivo
        self.editoresData["key"].value = tecla

    def dibujarAcciones(self, listaAcciones: list[dict], dispositivo: dispositivo) -> None:
        """Dibuja las acciones de los dispositivos en la interfaz web

        Args:
            listaAcciones (list[dict]): Lista de acciones a dibujar
        """

        def cabecera(texto: str, ancho: int, campo: str = None) -> None:
            if campo is None:
                ui.label(texto).style(f"font-weight: bold; width: {ancho}px")
                return
            if campo == self.ordenCampo:
                texto += " ▼" if self.ordenInverso else " ▲"
            etiqueta = ui.label(texto).style(f"font-weight: bold; width: {ancho}px; cursor: pointer")
            etiqueta.on("click", lambda c=campo: self.cambiarOrden(c, dispositivo))
            etiqueta.mark(f"orden-{campo}-{dispositivo.nombre}")

        with ui.row().classes("content p-2"):
            cabecera("Nombre", 100, "nombre")
            cabecera("Titulo", 100, "titulo")
            # ui.label("Imagen").style("font-weight: bold; width: 150px")
            cabecera("Tecla", 100, "key")
            cabecera("Acción", 125, "accion")
            cabecera("Opciones", 180)

        for acciónActual in self.ordenarAcciones(listaAcciones, self.ordenCampo, self.ordenInverso):
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

                marca = f"{dispositivo.nombre}-{teclaAcción}"
                with ui.button_group().props("rounded"):
                    ui.button(icon="play_arrow", color="teal-500", on_click=lambda a=acciónActual: self.buscarAccion(a, self.estadoTecla.PRESIONADA)).mark(f"ejecutar-{marca}")
                    ui.button(icon="edit", color="teal-500", on_click=lambda a=acciónActual: self.seleccionarAcción(a, dispositivo)).mark(f"editar-{marca}")
                    ui.button(icon="delete", color="teal-500", on_click=lambda a=acciónActual, d=dispositivo: self.borrarAcción(a, d)).mark(f"borrar-{marca}")

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
