"""Formulario para agregar o editar la acción de una tecla: datos, acción con sus opciones y apariencia del botón"""

import copy
import logging

import yaml
from nicegui import ui

from elGarrobo.accionesOOP import accion
from elGarrobo.dispositivos.dataAccion import dataAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.mideck.mi_streamdeck_plus import MiStreamDeckPlus
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.dialogos import dialogoPregunta
from elGarrobo.dispositivos.migui.editores import (
    avisarError,
    cargarOpciones,
    crearEditor,
    encabezado,
    leerOpciones,
    marcarError,
    nombrar,
)
from elGarrobo.dispositivos.migui.pasos import editorPasos
from elGarrobo.dispositivos.migui.teclas import ordenTecla, tamañoTecla, teclaRepetida
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__, logging.INFO)


class formularioAccion:
    """Formulario de la página de acciones; las pestañas lo usan con seleccionarAcción, nuevaAcciónTecla y siNoHayCambios"""

    def __init__(self, listaClasesAcciones: dict, listaDispositivos: list, pestañaActual, alGuardar, borrarConDeshacer, probarAcción) -> None:
        """Crea los widgets del formulario donde se llama (la columna izquierda de la página de acciones)

        Args:
            listaClasesAcciones (dict): comando → clase de la acción
            listaDispositivos (list): dispositivos conectados, para buscar el de la pestaña y el de entrar_folder
            pestañaActual: devuelve el nombre de la pestaña seleccionada, None si todavía no hay pestañas
            alGuardar: recibe el dispositivo después de cambiar sus acciones, para redibujar su pestaña
            borrarConDeshacer: borra una acción de un dispositivo con aviso para deshacer
            probarAcción: ejecuta una acción como si se presionara su tecla
        """
        self.listaClasesAcciones = listaClasesAcciones
        self.listaDispositivos = listaDispositivos
        self.pestañaActual = pestañaActual
        self.alGuardar = alGuardar
        self.borrarConDeshacer = borrarConDeshacer
        self.probarAcción = probarAcción
        self.accionEditar: dataAccion = None
        "Acción modificando, None si es una nueva"
        self.dispositivoEditar: dispositivo = None
        "Dispositivo de la acción editada; si es None se guarda en el de la pestaña seleccionada"
        self.opcionesEditar: dict[str, ui.element] = None
        self.formularioInicial: tuple = None
        "Valores del formulario al cargarlo, para avisar antes de descartar cambios"
        self.folderPendiente: tuple[dispositivo, str] = None
        "(dispositivo, folder) que se ofrece crear después de guardar un entrar_folder"

        self.pregunta = dialogoPregunta()

        self.pasos = editorPasos(self.listaClasesAcciones)

        self.tituloFormulario = ui.label("").classes("texto-acento font-bold px-2").mark("tituloFormulario")
        with ui.scroll_area().classes("w-full").style("height: 75vh"):

            # Campos de dataAccion marcados con gui, la clave del dict es la clave en el .md
            self.editoresData = {propiedad.atributo: crearEditor(propiedad, f"editor-{propiedad.atributo}").props("clearable") for propiedad in dataAccion.propiedadesGui()}

            # entrar_folder a un folder donde el dispositivo no tiene archivo de acciones
            with ui.dialog() as self.dialogoCrearFolder, ui.card():
                self.textoCrearFolder = ui.label("")
                with ui.row():
                    ui.button("Cancelar", on_click=self.dialogoCrearFolder.close).props("flat")
                    ui.button("Crear y entrar", icon="create_new_folder", color=tema.colorOscuro, on_click=self.crearFolderPendiente).mark("botonCrearFolder")

            # Apariencia del botón en un diálogo aparte para no llenar el formulario
            with ui.dialog() as self.dialogoBoton, ui.card():
                encabezado(ui.label("Apariencia del botón").classes("text-lg"), 2)
                with ui.row().classes("items-start"):
                    with ui.column().classes("w-64"):
                        self.editorTitulo = ui.input("Título", on_change=self.actualizarVistaPrevia).classes("w-full").props("clearable").mark("editor-titulo")
                        self.editorTituloMQTT = ui.input("Tópico MQTT del título", on_change=self.actualizarVistaPrevia).classes("w-full").props("clearable").mark("editor-titulo-mqtt")
                        self.editorTituloMQTT.props["hint"] = "El valor que llega reemplaza {} en el título, ej. {:.0f}%"
                        self.editorFondo = ui.color_input("Fondo", preview=True, on_change=self.actualizarVistaPrevia).classes("w-full").mark("editor-fondo")
                    self.vistaPrevia = ui.image().classes("w-24 h-24 rounded").props("fit=contain").mark("vistaPrevia")
                ui.button("Listo", color=tema.colorOscuro, on_click=self.dialogoBoton.close).mark("botonListoBoton")
            ui.button("Editar apariencia", icon="palette", color=tema.colorOscuro, on_click=self.abrirEditorApariencia).classes("w-full").mark("botonEditarBoton")

            self.listaNombreAcciones: list[str] = list()
            for clave in self.listaClasesAcciones.keys():
                claseAccion = self.listaClasesAcciones.get(clave)
                nombreAccion = claseAccion().nombre
                self.listaNombreAcciones.append(nombreAccion)

            self.editorAcción = ui.select(options=self.listaNombreAcciones, with_input=True, label="Acción", on_change=self.mostrarOpciones).classes("w-full").mark("editorAcción")
            self.pasos.catalogo.agregarBoton(self.editorAcción)
            self.editorDescripcion = ui.label("").classes(f"w-full bg-{tema.colorTecla} p-2 text-white rounded-lg")
            self.editorDescripcion.visible = False
            self.editorPropiedades = ui.column().classes("w-full")
            self.editorOpción = ui.textarea(label="Opciones (solo lectura, se conservan al guardar)").classes("w-full").props("readonly").mark("editorOpción")
            self.editorOpción.visible = False

        with ui.row().classes("items-center gap-2"):
            # Ícono + (agregar) o disquete (guardar cambios); el tooltip dice cuál
            self.botonAgregar = ui.button(icon="add", color=tema.colorOscuro, on_click=self.agregarAcción).props("rounded").mark("botonAgregar")
            with self.botonAgregar:
                self.tooltipAgregar = ui.tooltip()
            self.mostrarBotonGuardar(False)
            # Sueltos y no en button_group: con Ejecutar y Borrar ocultos el grupo deja Limpiar sin esquinas redondeadas
            # Ejecutar y Borrar solo se ven al editar una acción guardada
            self.botonEjecutar = ui.button(icon="play_arrow", color=tema.colorOscuro, on_click=self.ejecutarAcciónEditada).props("rounded").mark("botonEjecutar")
            nombrar(self.botonEjecutar, "Ejecutar acción guardada")
            nombrar(ui.button(icon="clear_all", color=tema.colorOscuro, on_click=lambda: self.siNoHayCambios(self.limpiarFormulario)).props("rounded").mark("botonLimpiar"), "Limpiar formulario")
            self.botonBorrar = ui.button(icon="delete", color=tema.colorPeligro, on_click=self.borrarAcciónEditada).props("rounded").mark("botonBorrar")
            nombrar(self.botonBorrar, "Borrar acción")
            self.botonEjecutar.visible = self.botonBorrar.visible = False

    def agregarAcción(self) -> None:
        """Agrega la acción nueva o guarda los cambios de la editada en su dispositivo"""
        self.limpiarErrores()
        # Los vacíos son None para no guardar claves vacías en el .md
        valores = {atributo: None if editor.value in ("", None) else editor.value for atributo, editor in self.editoresData.items()}
        nombre = valores["nombre"]
        tecla = valores["key"]
        acción = self.editorAcción.value
        acción = self.comandoAcción(acción) or acción
        nombreDispositivo = self.pestañaActual()

        if not nombreDispositivo:
            ui.notify("Selecciona un dispositivo", type="warning")
            return
        for propiedad in dataAccion.propiedadesGui():
            if propiedad.obligatorio and not valores[propiedad.atributo]:
                avisarError(self.editoresData[propiedad.atributo], f"Falta {propiedad.nombre}")
                return
        if not acción:
            avisarError(self.editorAcción, "Falta elegir la acción")
            return

        dispositivoDestino = self.dispositivoEditar or self.dispositivoSeleccionado(nombreDispositivo)
        if dispositivoDestino is None:
            ui.notify(f"No se encontró el dispositivo {nombreDispositivo}")
            return

        if dispositivoDestino.tipo in ["streamdeck", "streamdeckplus", "deck_combinado", "pedal"]:
            aparatos = getattr(dispositivoDestino, "listaDeck", [dispositivoDestino])
            conPlus = any(isinstance(aparato, MiStreamDeckPlus) for aparato in aparatos)
            try:
                tecla = valores["key"] = int(tecla)
            except ValueError:
                # Perillas y pantalla táctil del StreamDeck Plus: dial_1, touchscreen_1...
                if not (conPlus and MiStreamDeckPlus.patronControles.fullmatch(str(tecla))):
                    ejemplo = " o un control del Plus (dial_1, dial_derecho_1, touchscreen_1, deslizar_izquierda_1)" if conPlus else ""
                    avisarError(self.editoresData["key"], f"En {dispositivoDestino.nombre} la tecla es un número{ejemplo}")
                    return

        editando = self.accionEditar is not None
        repetida = teclaRepetida(dispositivoDestino.listaAcciones, tecla, self.accionEditar if editando else None)
        if repetida is not None:
            avisarError(self.editoresData["key"], f"La tecla {tecla} ya la usa '{repetida.get('nombre')}', elige otra")
            return

        # Antes de tocar la acción: si una opción no es válida la guardada queda igual, no a medias
        # (otro salvarAcciones del dispositivo escribiría el cambio parcial al .md)
        opciones = None
        if self.opcionesEditar is not None:
            try:
                opciones = leerOpciones(self.opcionesEditar, self.listaClasesAcciones.get(acción))
            except ValueError:
                return

        if editando:
            for atributo, valor in valores.items():
                self.accionEditar[atributo] = valor
            self.accionEditar["accion"] = acción
            self.aplicarApariencia(self.accionEditar)
            if opciones is not None:
                self.accionEditar["opciones"] = opciones

            ui.notify(f"{nombre} guardada en {dispositivoDestino.nombre}, tecla {tecla}", type="positive")
            logger.info(f"Editar acción {nombre} a {nombreDispositivo}")
        else:
            acciónNueva: dict[str:any] = {**valores, "accion": acción}
            if opciones is not None:
                acciónNueva["opciones"] = opciones

            acciónNueva = dataAccion.desdeDict(acciónNueva)
            self.aplicarApariencia(acciónNueva)
            dispositivoDestino.listaAcciones.append(acciónNueva)
            ui.notify(f"{nombre} agregada en {dispositivoDestino.nombre}, tecla {tecla}", type="positive")
            logger.info(f"Agregando acción {nombre} a {nombreDispositivo}")

        guardada = self.accionEditar if editando else acciónNueva
        dispositivoDestino.listaAcciones.sort(key=ordenTecla)
        dispositivoDestino.salvarAcciones()
        self.alGuardar(dispositivoDestino)
        self.limpiarFormulario()
        self.ofrecerCrearFolder(guardada, dispositivoDestino)

    def mostrarBotonGuardar(self, editando: bool) -> None:
        """Agregar para una acción nueva, Guardar cambios al editar una guardada"""
        texto = "Guardar cambios" if editando else "Agregar acción"
        self.botonAgregar.icon = "save" if editando else "add"
        self.botonAgregar.props["aria-label"] = texto
        self.tooltipAgregar.text = texto

    def mostrarOpciones(self):
        """Muestra las opciones de la acción seleccionada"""
        self.editorDescripcion.text = ""
        self.editorDescripcion.visible = False
        # Guarda los valores para pasarlos a las propiedades con el mismo nombre de la nueva acción
        valoresAnteriores = {nombre: (editor.tipoEditor, editor.value) for nombre, editor in (self.opcionesEditar or {}).items()}
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
                    editor = crearEditor(propiedad, f"opción-{nombre}")
                    # El aviso de ruta busca ./x en el folder que se edita, igual que al ejecutarla
                    editor.folderRuta = getattr(self.dispositivoEditar, "folderActual", None)
                    tipoAnterior, valorAnterior = valoresAnteriores.get(nombre, (None, None))
                    if valorAnterior and tipoAnterior == editor.tipoEditor:
                        editor.value = valorAnterior
                    self.opcionesEditar[nombre] = editor
                    if propiedad.atributo == acciónTmp.atributoLista:
                        ui.button("Editar pasos", icon="view_list", color=tema.colorOscuro, on_click=lambda e=editor: self.pasos.abrir(e)).classes("w-full").mark("botonEditarPasos")
            return

        logger.warning(f"No hay opciones para: {accionSeleccionada}")

    def limpiarErrores(self) -> None:
        for editor in [*self.editoresData.values(), self.editorAcción, *(self.opcionesEditar or {}).values()]:
            marcarError(editor, None)

    def estadoFormulario(self) -> tuple:
        """Foto de los valores del formulario, para saber si hay cambios sin guardar"""
        editores = [*self.editoresData.values(), self.editorTitulo, self.editorTituloMQTT, self.editorFondo, self.editorAcción, *(self.opcionesEditar or {}).values()]
        return tuple(str(editor.value) for editor in editores)

    def recordarFormulario(self) -> None:
        self.formularioInicial = self.estadoFormulario()
        self.actualizarTituloFormulario()

    @staticmethod
    def mostrarFormularioEnCelular() -> None:
        """En celular/tablet el formulario queda debajo del dispositivo: se lleva a la vista al elegir una tecla"""
        ui.run_javascript("if (innerWidth < 1024) document.querySelector('.formulario-gui')?.scrollIntoView({behavior: 'smooth'})")

    def hayCambios(self) -> bool:
        return self.formularioInicial is not None and self.estadoFormulario() != self.formularioInicial

    def siNoHayCambios(self, funcion) -> None:
        """Ejecuta funcion, o antes pregunta si descartar los cambios sin guardar del formulario"""
        if not self.hayCambios():
            funcion()
            return
        nombre = f"'{self.accionEditar.get('nombre')}'" if self.accionEditar else "la acción nueva"
        self.pregunta.preguntar(f"Hay cambios sin guardar en {nombre}. ¿Descartarlos?", "Descartar", funcion)

    def actualizarTituloFormulario(self) -> None:
        """Dice arriba del formulario qué se está editando y en qué dispositivo se guardará"""
        if self.tituloFormulario is None:
            return
        destino = self.dispositivoEditar or self.dispositivoSeleccionado()
        enDispositivo = f" · {destino.nombre}" if destino else ""
        if self.accionEditar is not None:
            self.tituloFormulario.text = f"Editando '{self.accionEditar.get('nombre')}'{enDispositivo} · tecla {self.accionEditar.get('key')}"
        else:
            tecla = self.editoresData["key"].value
            self.tituloFormulario.text = f"Nueva acción{enDispositivo}" + (f" · tecla {tecla}" if tecla not in ("", None) else "")

    def comandoAcción(self, nombreAcción: str) -> str | None:
        """Comando de la acción a partir del nombre que muestra el selector"""
        for claseAcción in self.listaClasesAcciones.values():
            objetoClase: accion = claseAcción()
            if objetoClase.nombre == nombreAcción:
                return objetoClase.comando
        return None

    def abrirEditorApariencia(self) -> None:
        # Sin apariencia todavía: el nombre sirve de título para configurarlo más rápido
        if not (self.editorTitulo.value or self.editorTituloMQTT.value or self.editorFondo.value):
            self.editorTitulo.value = self.editoresData["nombre"].value or ""
        self.actualizarVistaPrevia()
        self.dialogoBoton.open()

    def actualizarVistaPrevia(self, *_) -> None:
        """Dibuja el botón con lo que hay en el formulario, sin guardar"""
        dispositivoActual = self.dispositivoEditar or self.dispositivoSeleccionado()
        if dispositivoActual is None:
            return

        # Copia profunda: imagen_opciones es un dict y aplicarApariencia lo modifica, no debe tocar la acción guardada
        acción = copy.deepcopy(self.accionEditar) if self.accionEditar else dataAccion()
        acción.accion = self.comandoAcción(self.editorAcción.value) or acción.accion
        self.aplicarApariencia(acción)
        # En teclados cada tecla mide distinto, se usa la medida de la tecla editada
        tecla = str(self.editoresData["key"].value)
        teclaFisica = next((t for t in dispositivoActual.distribucionTeclas() or [] if t["key"] == tecla), None)
        tamaño = tamañoTecla(teclaFisica) if teclaFisica else dispositivoActual.tamañoBoton()
        try:
            dibujo = dispositivoActual.dibujo()
            fps = getattr(dispositivoActual, "fps", None)
            imagen = dibujo.dibujarAnimado(acción, tamaño, fps=fps) or dibujo.dibujar(acción, tamaño, conGif=True)
        except Exception as error:
            # Ej: color a medio escribir, se deja la vista previa anterior
            logger.debug(f"Vista previa[Error] {error}")
            return
        self.vistaPrevia.set_source(imagen)

    def aplicarApariencia(self, acción: dataAccion) -> None:
        """Pasa a la acción el título, tópico MQTT del título y fondo del editor del botón"""
        acción.titulo = self.editorTitulo.value or None
        acción.fondo = self.editorFondo.value or None
        if self.editorTituloMQTT.value:
            acción.tituloOpciones["mqtt"] = self.editorTituloMQTT.value
        else:
            acción.tituloOpciones.pop("mqtt", None)

    def limpiarFormulario(self):
        """Limpia el formulario de acciones"""
        self.mostrarBotonGuardar(False)
        self.botonEjecutar.visible = self.botonBorrar.visible = False
        for editor in self.editoresData.values():
            editor.value = ""
        self.editorTitulo.value = ""
        self.editorTituloMQTT.value = ""
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
        self.limpiarErrores()
        self.recordarFormulario()

    def ejecutarAcciónEditada(self) -> None:
        acción, dispositivo = self.accionEditar, self.dispositivoEditar
        # Se revisa antes: si el folder existe el dispositivo entra y la ruta relativa ya no sirve
        faltaFolder = self.folderFaltante(acción, dispositivo)
        self.probarAcción(acción, dispositivo)
        if faltaFolder:
            self.ofrecerCrearFolder(acción, dispositivo)

    def folderFaltante(self, acción: dataAccion, dispositivo: dispositivo) -> tuple[dispositivo, str] | None:
        """(dispositivo, folder) si la acción es entrar_folder y ese dispositivo no tiene archivo de acciones ahí"""
        if acción is None:
            return None
        opciones = acción.get("opciones")
        if acción.get("accion") != "entrar_folder" or not isinstance(opciones, dict) or not opciones.get("folder"):
            return None
        # Con 'dispositivo' en las opciones el folder es de ese dispositivo, no del que se edita
        if opciones.get("dispositivo"):
            nombre = opciones["dispositivo"].lower()
            dispositivo = next((d for d in self.listaDispositivos if d.nombre.lower() == nombre), None)
        if dispositivo is None or dispositivo.tieneFolder(opciones["folder"]):
            return None
        return dispositivo, opciones["folder"]

    def ofrecerCrearFolder(self, acción: dataAccion, dispositivo: dispositivo) -> None:
        """Pregunta si crear el folder de un entrar_folder cuando el dispositivo no tiene acciones ahí"""
        self.folderPendiente = self.folderFaltante(acción, dispositivo)
        if self.folderPendiente is None:
            return
        dispositivo, folder = self.folderPendiente
        self.textoCrearFolder.text = f"{dispositivo.nombre} no tiene acciones en {folder}. ¿Crear el folder y entrar?"
        self.dialogoCrearFolder.open()

    def crearFolderPendiente(self) -> None:
        dispositivo, folder = self.folderPendiente
        dispositivo.crearFolder(folder)
        self.dialogoCrearFolder.close()
        ui.notify(f"Folder {folder} creado en {dispositivo.nombre}")
        self.alGuardar(dispositivo)

    def borrarAcciónEditada(self) -> None:
        """Borra la acción que está en el editor y lo limpia"""
        self.borrarConDeshacer(self.accionEditar, self.dispositivoEditar, antes=self.limpiarFormulario)

    def seleccionarAcción(self, accion: dict, dispositivo: dispositivo = None):
        if dispositivo is not None:
            self.dispositivoEditar = dispositivo
        else:
            self.dispositivoEditar = None

        self.accionEditar = accion
        self.limpiarErrores()
        self.mostrarFormularioEnCelular()
        self.mostrarBotonGuardar(True)
        self.botonEjecutar.visible = self.botonBorrar.visible = True
        for atributo, editor in self.editoresData.items():
            editor.value = accion.get(atributo)
        self.editorTitulo.value = accion.titulo or ""
        self.editorTituloMQTT.value = accion.tituloOpciones.get("mqtt") or ""
        self.editorFondo.value = accion.fondo or ""

        # Sin esto mostrarOpciones pasaría los valores de la acción editada antes
        self.opcionesEditar = None
        claseAcción = self.listaClasesAcciones.get(accion.get("accion"))
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

            if claseAcción is not None:
                cargarOpciones(self.opcionesEditar, claseAcción, opcionesActuales)
            else:
                # Sin editor para estas opciones (ej. pasos de una macro): se muestran y se guardan sin cambios
                self.editorOpción.visible = True
                self.editorOpción.value = yaml.safe_dump(opcionesActuales, allow_unicode=True, sort_keys=False)
        self.recordarFormulario()

    def nuevaAcciónTecla(self, dispositivo: dispositivo, tecla: int) -> None:
        """Prepara el formulario para agregar una acción en una tecla vacía de la cuadrícula"""
        self.limpiarFormulario()
        self.dispositivoEditar = dispositivo
        self.editoresData["key"].value = tecla
        self.recordarFormulario()
        self.mostrarFormularioEnCelular()

    def dispositivoSeleccionado(self, nombreDispositivo: str = None) -> dispositivo:
        """Dispositivo de la pestaña (por defecto la seleccionada), None si no hay"""
        nombreDispositivo = nombreDispositivo or self.pestañaActual()
        return next((d for d in self.listaDispositivos if d.nombre == nombreDispositivo), None)
