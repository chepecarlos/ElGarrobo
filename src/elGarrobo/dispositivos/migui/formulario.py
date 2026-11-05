"""Formulario para agregar o editar la acción de una tecla: datos, acción con sus opciones y apariencia del botón"""

import copy
import io
import logging
from pathlib import Path

import yaml
from nicegui import ui
from PIL import Image

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
    enlazarOcultos,
    encabezado,
    leerOpciones,
    marcarError,
    nombrar,
    ponerValor,
)
from elGarrobo.dispositivos.migui.pasos import editorPasos
from elGarrobo.dispositivos.migui.teclas import ordenTecla, tamañoTecla, teclaRepetida
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__, logging.INFO)

extensionesImagen = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def imágenesDisponibles(folderPerfil: Path, folder: Path) -> list[str]:
    """Imágenes del folder (sin /) y de la raíz del perfil (con /), escritas como en la clave imagen del .md"""

    def imágenes(carpeta: Path) -> list[str]:
        return sorted(a.name for a in carpeta.glob("*") if a.suffix.lower() in extensionesImagen and a.is_file())

    raíz = [] if folder == folderPerfil else [f"/{nombre}" for nombre in imágenes(folderPerfil)]
    return imágenes(folder) + raíz


def valorVacío(editor: ui.element) -> str | None:
    """Valor de un editor vacío: number y select usan None, los de texto "" (color_input falla con None)"""
    return None if isinstance(editor, (ui.number, ui.select)) else ""


def guardarImagen(folder: Path, nombre: str, datos: bytes) -> str:
    """Copia una imagen subida al folder y devuelve su nombre ahí
    Si ya hay otra con ese nombre se guarda como nombre-1.png, si es la misma se reutiliza

    Raises:
        ValueError: si no tiene extensión de imagen
        Exception: de PIL si el contenido no es una imagen
    """
    # Solo el nombre: "../x.png" no debe escribir fuera del folder
    archivo = Path(Path(nombre).name)
    if archivo.suffix.lower() not in extensionesImagen:
        raise ValueError(f"{nombre} no tiene extensión de imagen")
    Image.open(io.BytesIO(datos)).verify()

    destino, número = folder / archivo, 1
    while destino.exists() and destino.read_bytes() != datos:
        destino = folder / f"{archivo.stem}-{número}{archivo.suffix}"
        número += 1
    if not destino.exists():
        folder.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(datos)
    return destino.name


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
                        # Vacíos usan el valor del folder o el de dibujoBoton.ponerTexto
                        colorTexto = ui.color_input("Color del texto", preview=True, on_change=self.actualizarVistaPrevia).classes("w-full").mark("editor-titulo-color")
                        colorBorde = ui.color_input("Color del borde", preview=True, on_change=self.actualizarVistaPrevia).classes("w-full").mark("editor-titulo-borde-color")
                        alinear = ui.select({"arriba": "Arriba", "centro": "Centro", "abajo": "Abajo"}, label="Alineación del título", clearable=True, on_change=self.actualizarVistaPrevia)
                        alinear.classes("w-full").mark("editor-titulo-alinear").props["hint"] = "Vacía: abajo con imagen, al centro sin imagen"
                        with ui.expansion("Más opciones del título").classes("w-full").props("dense").mark("masOpcionesTitulo"):
                            grosor = ui.number("Grosor del borde", min=0, precision=0, placeholder="6", on_change=self.actualizarVistaPrevia).classes("w-full").mark("editor-titulo-borde-grosor")
                            with ui.row().classes("w-full no-wrap gap-2"):
                                mínimo = ui.number("Letra mínima", min=1, precision=0, on_change=self.actualizarVistaPrevia).classes("flex-1").mark("editor-titulo-tamanno-minimo")
                                máximo = ui.number("Letra máxima", min=1, precision=0, on_change=self.actualizarVistaPrevia).classes("flex-1").mark("editor-titulo-tamanno-maximo")
                        self.editoresTitulo: dict[str, ui.element] = {
                            "mqtt": self.editorTituloMQTT,
                            "color": colorTexto,
                            "borde_color": colorBorde,
                            "alinear": alinear,
                            "borde_grosor": grosor,
                            "tamanno_minimo": mínimo,
                            "tamanno_maximo": máximo,
                        }
                        "Clave en titulo_opciones → su editor"
                        self.editorFondo = ui.color_input("Fondo", preview=True, on_change=self.actualizarVistaPrevia).classes("w-full").mark("editor-fondo")
                        # El navegador no da la ruta del archivo, solo su contenido: se copia al folder actual
                        # Oculto porque su lista de archivos ocupa mucho, se abre con el botón junto al selector
                        self.subidorImagen = (
                            ui.upload(auto_upload=True, max_file_size=20_000_000, on_upload=self.subirImagen, on_rejected=lambda: ui.notify("Imagen muy grande, máximo 20 MB", type="warning"))
                            .props('accept="image/*"')
                            .classes("hidden")
                        )
                        with ui.row().classes("w-full items-center no-wrap gap-1"):
                            self.editorImagen = ui.select([], label="Imagen", new_value_mode="add-unique", clearable=True, on_change=self.actualizarVistaPrevia).classes("grow").mark("editor-imagen")
                            self.editorImagen.props["hint"] = "Sin / en el folder actual, con / desde la raíz del perfil"
                            botonSubir = ui.button(icon="upload", color=tema.colorOscuro, on_click=lambda: self.subidorImagen.run_method("pickFiles")).props("round").mark("subirImagen")
                            nombrar(botonSubir, "Subir imagen al folder actual")
                        with ui.column().classes("w-full gap-0").bind_visibility_from(self.editorImagen, "value", backward=bool):
                            self.editorEscala = ui.slider(min=10, max=100, step=5, value=100, on_change=self.actualizarVistaPrevia).classes("w-full").mark("editor-escala")
                            ui.label().bind_text_from(self.editorEscala, "value", backward=lambda valor: f"Tamaño de la imagen: {valor}%").classes("text-sm")
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
                        # El texto YAML ya está armado; los demás por ponerValor (un select no acepta valores fuera de su lista)
                        if editor.tipoEditor == "yaml":
                            editor.value = valorAnterior
                        else:
                            ponerValor(editor, valorAnterior)
                    self.opcionesEditar[nombre] = editor
                    if propiedad.atributo == acciónTmp.atributoLista:
                        self.pasos.agregarBoton(editor)
                enlazarOcultos(self.opcionesEditar)
            return

        logger.warning(f"No hay opciones para: {accionSeleccionada}")

    def limpiarErrores(self) -> None:
        for editor in [*self.editoresData.values(), self.editorAcción, *(self.opcionesEditar or {}).values()]:
            marcarError(editor, None)

    def estadoFormulario(self) -> tuple:
        """Foto de los valores del formulario, para saber si hay cambios sin guardar"""
        editores = [*self.editoresData.values(), self.editorTitulo, *self.editoresTitulo.values(), self.editorFondo, self.editorImagen, self.editorEscala, self.editorAcción, *(self.opcionesEditar or {}).values()]
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
        if not (self.editorTitulo.value or self.editorTituloMQTT.value or self.editorFondo.value or self.editorImagen.value):
            self.editorTitulo.value = self.editoresData["nombre"].value or ""
        # Las imágenes del folder pudieron cambiar desde que se cargó la acción
        self.mostrarImagen(self.editorImagen.value)
        self.actualizarVistaPrevia()
        self.dialogoBoton.open()

    def foldersImagen(self) -> tuple[Path, Path] | None:
        """(folder del perfil, folder actual) del dispositivo editado, None si no hay dispositivo"""
        dispositivoActual = self.dispositivoEditar or self.dispositivoSeleccionado()
        if dispositivoActual is None:
            return None
        folderPerfil = dispositivoActual._folderConfigPerfil()
        return folderPerfil, folderPerfil / str(dispositivoActual.folderActual).lstrip("/")

    def mostrarImagen(self, imagen: str | None) -> None:
        """Pone la imagen en el selector con las del folder editado, aunque no esté entre ellas (ej. /pulse/mic.png)"""
        folders = self.foldersImagen()
        opciones = imágenesDisponibles(*folders) if folders else []
        if imagen and imagen not in opciones:
            opciones.append(imagen)
        self.editorImagen.set_options(opciones, value=imagen or None)

    async def subirImagen(self, evento) -> None:
        """Copia la imagen subida al folder actual del dispositivo y la elige para el botón"""
        self.subidorImagen.reset()
        folders = self.foldersImagen()
        if folders is None:
            ui.notify("Selecciona un dispositivo", type="warning")
            return
        try:
            nombre = guardarImagen(folders[1], evento.file.name, await evento.file.read())
        except Exception as error:
            logger.warning(f"Imagen[Error] {evento.file.name} - {error}")
            ui.notify(f"{evento.file.name} no es una imagen", type="warning")
            return
        self.mostrarImagen(nombre)
        ui.notify(f"Imagen {nombre} copiada a {folders[1]}", type="positive")

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
        """Pasa a la acción el título, sus opciones (titulo_opciones), fondo e imagen del editor del botón"""
        acción.titulo = self.editorTitulo.value or None
        acción.fondo = self.editorFondo.value or None
        acción.imagen = self.editorImagen.value or None
        if self.editorEscala.value < 100:
            acción.imagenOpciones["escala"] = self.editorEscala.value
        else:
            acción.imagenOpciones.pop("escala", None)
        for clave, editor in self.editoresTitulo.items():
            valor = editor.value
            if valor in ("", None):
                acción.tituloOpciones.pop(clave, None)
            else:
                # ui.number da float (40.0), en el .md va como entero
                acción.tituloOpciones[clave] = int(valor) if isinstance(valor, float) else valor

    def limpiarFormulario(self):
        """Limpia el formulario de acciones"""
        self.mostrarBotonGuardar(False)
        self.botonEjecutar.visible = self.botonBorrar.visible = False
        for editor in self.editoresData.values():
            editor.value = ""
        self.editorTitulo.value = ""
        for editor in self.editoresTitulo.values():
            editor.value = valorVacío(editor)
        self.editorFondo.value = ""
        self.editorImagen.set_options([], value=None)
        self.editorEscala.value = 100
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
        for clave, editor in self.editoresTitulo.items():
            valor = accion.tituloOpciones.get(clave)
            # Un valor escrito a mano en el .md que no está en el selector se agrega para no perderlo
            if isinstance(editor, ui.select) and valor is not None and valor not in editor.options:
                editor.set_options({**editor.options, valor: valor})
            editor.value = valorVacío(editor) if valor is None else valor
        self.editorFondo.value = accion.fondo or ""
        self.mostrarImagen(accion.imagen)
        self.editorEscala.value = accion.imagenOpciones.get("escala", 100)

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
