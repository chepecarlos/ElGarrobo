import base64
import copy
import hashlib
import io
import logging
import threading
from pathlib import Path

import yaml
from fastapi import Response
from nicegui import app, ui

from elGarrobo.accionesOOP import accion
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.dispositivos.dataAccion import dataAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.mideck.mi_streamdeck_plus import MiStreamDeckPlus
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerArchivo, SalvarArchivo, SalvarValor, leerData

# librería https://nicegui.io/
# estilo https://tailwindcss.com/
# iconos https://fonts.google.com/icons


logger = ConfigurarLogging(__name__, logging.INFO)

ARCHIVO_PREFERENCIAS = "gui_preferencias"
"Archivo de config con preferencias de la GUI (ej. el último modo Usar/Editar)"

COLORES_QUASAR = {"primary": "#00786f", "negative": "#dc2626", "positive": "#15803d"}
"Colores de Quasar con texto blanco encima ≥4.5:1 (los de NiceGUI daban 3.1, 2.6 y 2.5); primary es teal-700 como colorBotones"

_vistas: dict[str, tuple[bytes, str]] = {}
"hash → (contenido, tipo) de las vistas previas de las teclas, las sirve /vista/{hash}"
_candadoVistas = threading.Lock()
"Los dispositivos redibujan la GUI desde sus hilos"
MAXIMO_VISTAS = 1024


def urlVista(imagen) -> str:
    """URL de la vista previa (imagen PIL o data URI de dibujarAnimado) con el hash de su contenido.

    El navegador la guarda en caché: al redibujar una pestaña solo viaja la ruta y no la imagen en base64
    """
    if isinstance(imagen, str):
        tipo, datos = imagen.removeprefix("data:").split(";base64,", 1)
        contenido = base64.b64decode(datos)
    else:
        buffer = io.BytesIO()
        imagen.save(buffer, "PNG")
        contenido, tipo = buffer.getvalue(), "image/png"
    nombre = hashlib.sha1(contenido).hexdigest()
    with _candadoVistas:
        _vistas.pop(nombre, None)
        _vistas[nombre] = (contenido, tipo)
        # ponytail: se borra la más vieja; una pestaña abierta mucho tiempo que no la tenga en caché la vería rota hasta redibujar
        if len(_vistas) > MAXIMO_VISTAS:
            del _vistas[next(iter(_vistas))]
    return f"/vista/{nombre}"


def servirVista(nombre: str) -> Response:
    vista = _vistas.get(nombre)
    if vista is None:
        return Response(status_code=404)
    # El nombre es el hash del contenido: nunca cambia, el navegador no vuelve a pedirla
    return Response(vista[0], media_type=vista[1], headers={"Cache-Control": "public, max-age=31536000, immutable"})

CSS_BOTONERA = """
/* Únicos colores fijos del CSS: el fondo de la carcasa, el foco (teal-300, mismo que colorClaro) y el texto de error */
:root { --color-carcasa: #0b1716; --color-foco: #5eead4; --color-error-texto: #f87171; }
/* primary y negative (ver COLORES_QUASAR) son fondos con texto blanco; como texto sobre el fondo oscuro no llegan a 4.5:1.
   En campos, menús y botones planos se usa el teal claro y un rojo claro para la etiqueta, la opción elegida y los errores */
.q-field, .q-menu, .q-btn--flat { --q-primary: var(--color-foco); }
.q-field { --q-negative: var(--color-error-texto); }
.modo-usar > .q-splitter__separator { display: none; }
.carcasa {
    background: var(--color-carcasa);
    border-radius: 1.75rem;
    padding: 1.5rem;
    box-shadow: 0 18px 40px -12px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
.tecla-viva { touch-action: none; user-select: none; -webkit-touch-callout: none; transition: transform 90ms cubic-bezier(0.16, 1, 0.3, 1), filter 90ms cubic-bezier(0.16, 1, 0.3, 1); }
.tecla-viva:active { transform: scale(0.94); filter: brightness(1.35); }
/* Foco con teclado visible en todo lo que se presiona: el tinte de Quasar casi no se ve sobre los botones teal.
   Quasar pone .no-outline { outline: 0 !important } en q-btn y q-toggle (las teclas también son q-btn) dentro de la capa
   quasar_importants; con !important gana la capa declarada antes, por eso esta va en base y no suelta */
@layer base {
    .tecla-viva:focus-visible, .opcion-distribucion:focus-visible, .q-btn:focus-visible, .q-toggle:focus-visible, .q-item:focus-visible { outline: 2px solid var(--color-foco) !important; outline-offset: 3px; }
}
.q-tab:focus-visible { outline: 2px solid var(--color-foco); outline-offset: -2px; }
/* Navegar: la página entra desde el lado hacia donde se fue (adentro/siguiente → derecha, arriba/anterior → izquierda) */
@keyframes navega-entra { from { opacity: 0.3; transform: translateX(16px); } }
@keyframes navega-sale { from { opacity: 0.3; transform: translateX(-16px); } }
@keyframes navega-funde { from { opacity: 0.3; } }
.navega-entra { animation: navega-entra 220ms cubic-bezier(0.16, 1, 0.3, 1); }
.navega-sale { animation: navega-sale 220ms cubic-bezier(0.16, 1, 0.3, 1); }
@media (prefers-reduced-motion: reduce) {
    .tecla-viva { transition: none; }
    .navega-entra, .navega-sale { animation: navega-funde 160ms ease-out; }
}
/* Celular y tablet: el splitter deja el formulario en 20% del ancho, se apila debajo del dispositivo */
@media (max-width: 1023px) {
    .pagina-acciones.q-splitter { flex-direction: column; }
    .pagina-acciones > .q-splitter__panel { width: 100% !important; }
    .pagina-acciones > .q-splitter__before { order: 2; }
    .pagina-acciones > .q-splitter__separator { display: none; }
}
/* Escritorio: las pestañas de dispositivos van en la cabecera, en una grilla con los lados iguales para que
   no se muevan cuando cambia el folder o la última acción; en pantallas angostas bajan a una segunda fila.
   --alto-cabecera lo actualiza un ResizeObserver (paginaAcciones) para que los altos en vh no dependan de las filas */
:root { --alto-cabecera: 48px; }
.cabecera-grilla { display: grid !important; grid-template-columns: minmax(0, 1fr) minmax(0, max-content) minmax(0, 1fr); }
@media (max-width: 1023px) {
    .cabecera-grilla { grid-template-columns: auto minmax(0, 1fr); }
    .cabecera-pestañas { order: 99; grid-column: 1 / -1; }
}
/* Dedo: botones e interruptores llegan a 44px; las teclas no, miden lo que mide la tecla del aparato */
@media (pointer: coarse) {
    .q-btn:not(.tecla-viva), .q-toggle { min-height: 44px; }
    .q-btn--round:not(.tecla-viva) { min-width: 44px; }
}
/* Vista lista: cada fila es su propia grilla, la columna de botones es fija para que todas midan igual; en celular se ocultan Título y Acción */
.fila-acciones { width: 100%; display: grid; grid-template-columns: minmax(6rem, 2fr) minmax(5rem, 1.5fr) minmax(3.5rem, 1fr) minmax(6rem, 1.5fr) 10.25rem; gap: 0.5rem; align-items: center; }
.fila-acciones > * { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fila-acciones > *:last-child { overflow: visible; }
@media (max-width: 639px) {
    .fila-acciones { grid-template-columns: minmax(3rem, 1fr) 2.5rem 10.25rem; gap: 0.25rem; }
    .cabecera-acciones > * { overflow: visible; }
    .fila-acciones > .solo-ancho { display: none; }
}
"""


class miGui(dispositivo):
    """
    Interfaz web de ElGarrobo
    """

    nombre = "Interfaz Gráfica"
    modulo = "gui"
    tipo = "gui"
    descripcion = "Interfaz web/gráfica (GUI) de ElGarrobo"
    archivoConfiguracion = "gui.md"
    icono = "web"

    listaDispositivos: list[dispositivo] = None
    "Lista de dispositivos conectados"

    accionEditar: dict
    "Acción modificando o agregando"
    dispositivoEditar: dispositivo
    "dispositivo a modificar la acción"

    # Roles de color: usar estos y no colores sueltos. Los que llevan texto blanco deben dar ≥4.5:1
    colorOscuro: str = "teal-900"
    "Cabecera, pestañas y botones del formulario"
    colorClaro: str = "teal-300"
    "Texto e íconos de acento sobre fondo oscuro"
    colorBotones: str = "teal-700"
    "Botones de herramientas (subir, página, intercambiar…): blanco sobre teal-700 ≈ 5.3:1 (teal-500 daba 2.4:1)"
    colorTecla: str = "teal-700"
    "Tecla con acción en teclados y botonera, con su nombre en texto blanco"
    colorTeclaVacia: str = "grey-8"
    "Tecla sin acción"
    colorActivo: str = "orange-700"
    "Herramienta encendida (modo intercambiar): blanco sobre orange-700 ≈ 5.2:1"
    colorPeligro: str = "negative"
    "Borrar, descartar, confirmar salir/reiniciar y errores"
    colorBorde: str = "teal-600"
    "Bordes decorativos de paneles y filas (sin texto encima)"
    colorTeclaApagada: str = "grey-10"
    "Tecla sin acción en modo Usar: casi invisible, no se puede presionar"
    colorSeleccion: str = "teal-4"
    "Opción elegida en los interruptores (Usar/Editar, Cuadrícula/Lista), con texto negro"
    colorInterruptor: str = "teal-10"
    "Fondo de la opción no elegida del interruptor Usar/Editar sobre la cabecera"

    puerto: int = 8080
    "puerto de la interfaz web"

    folderLabel: ui.label = None
    "Etiqueta con el dispositivo y folder actual"
    ultimaLabel: ui.label = None
    "Etiqueta con la última acción ejecutada en modo Usar"

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
        "Dispositivos con distribución física que el usuario cambió a vista de lista"
        self.dispositivoFolder = None
        "Dispositivo cuyas propiedades del folder se están editando"
        self.ordenInverso: bool = False
        self.teclaIntercambio: dict = {}
        "Dispositivos en modo intercambiar → primera tecla seleccionada (None si aún no hay)"
        self.acciónDuplicar: dict[str, dataAccion | None] = {}
        "dispositivo → acción a copiar en modo duplicar; guarda la acción y no la tecla para poder pegarla en otra página o folder"
        self.teclasPresionadas: dict[int, dataAccion] = {}
        "id → acción presionada en modo Usar, para mandar soltar una sola vez"
        self.teclasDibujadas: dict[str, dict[str, tuple[ui.element, dataAccion | None]]] = {}
        "dispositivo → tecla → (botón, acción) de la cuadrícula en Editar, para marcar la selección sin redibujar"
        self.herramientasModo: dict[str, dict[str, ui.button]] = {}
        "dispositivo → botones Intercambiar y Duplicar de la barra, para pintarlos sin redibujar"
        self.últimaVista: dict[str, tuple[Path, int]] = {}
        "dispositivo → (folder, página) dibujados la última vez, para saber hacia dónde se navegó"
        self.modoUsar: bool = False
        "Modo Usar: click en una tecla la ejecuta; modo Editar: la abre en el formulario"
        self.splitter: ui.splitter = None
        self.tituloFormulario: ui.label = None
        self.formularioInicial: tuple = None
        "Valores del formulario al cargarlo, para avisar antes de descartar cambios"
        self.funcionPregunta = None
        self.contenedorFormulario: ui.column = None
        self.borrados: dict[int, tuple] = {}
        "id del aviso → (acción, dispositivo, folder, posición) que todavía se puede deshacer"
        self.contadorBorrados: int = 0

        self.listaDispositivos = list()

        app.get("/vista/{nombre}")(servirVista)

        @ui.page("/")
        def paginaAcciones() -> None:
            """Estructura de pagina de acciones"""
            from elGarrobo.accionesOOP.accionListaCheckBox import accionListaCheckBox

            accionListaCheckBox.registrarCliente(ui.context.client)
            # Cambiar de ventana con una tecla presionada no manda pointerup: se suelta todo al perder el foco
            ui.add_body_html("<script>window.addEventListener('blur', () => emitEvent('ventanaSinFoco'))</script>")
            ui.on("ventanaSinFoco", self.soltarTodas)
            # Con timer y no add_body_html: la cabecera todavía no existe cuando corre el html del body
            ui.timer(
                0,
                lambda: ui.run_javascript(
                    "new ResizeObserver(([e]) => document.documentElement.style.setProperty('--alto-cabecera', "
                    "e.target.offsetHeight + 'px')).observe(document.querySelector('.q-header'))"
                ),
                once=True,
            )
            ui.on("deshacerBorrar", lambda e: self.deshacerBorrar(e.args))

            # Límite inferior 0: en modo Usar el formulario se oculta y el aparato ocupa todo el ancho
            with ui.splitter(value=20, limits=(0, 50)) as self.splitter:
                self.splitter.classes("w-full pagina-acciones")
                with self.splitter.before:
                    with ui.column().classes("w-full formulario-gui") as self.contenedorFormulario:
                        self.mostrarFormulario()
                with self.splitter.after:
                    self.pestañas = ui.tabs(on_change=self.actualizarCabecera).props("outside-arrows mobile-arrows")
                    # Se mueven a la cabecera en estructura()
                    self.pestañas.classes("cabecera-pestañas text-white")
                    self.paneles = ui.tab_panels(self.pestañas)
                    self.paneles.classes("w-full")
                    self.crearPestañas()
            self.estructura(conModo=True)
            self.aplicarModo()
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
            self.limpiarErrores()
            # Los vacíos son None para no guardar claves vacías en el .md
            valores = {atributo: None if editor.value in ("", None) else editor.value for atributo, editor in self.editoresData.items()}
            nombre = valores["nombre"]
            tecla = valores["key"]
            acción = self.editorAcción.value
            acción = self.comandoAcción(acción) or acción
            nombreDispositivo = self.pestañas.value

            if not nombreDispositivo:
                ui.notify("Selecciona un dispositivo", type="warning")
                return
            for propiedad in dataAccion.propiedadesGui():
                if propiedad.obligatorio and not valores[propiedad.atributo]:
                    self.avisarError(self.editoresData[propiedad.atributo], f"Falta {propiedad.nombre}")
                    return
            if not acción:
                self.avisarError(self.editorAcción, "Falta elegir la acción")
                return

            dispositivoDestino = self.dispositivoEditar or self.obtenerDispositivoSeleccionado(nombreDispositivo)
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
                        self.avisarError(self.editoresData["key"], f"En {dispositivoDestino.nombre} la tecla es un número{ejemplo}")
                        return

            editando = self.accionEditar is not None
            repetida = self.teclaRepetida(dispositivoDestino.listaAcciones, tecla, self.accionEditar if editando else None)
            if repetida is not None:
                self.avisarError(self.editoresData["key"], f"La tecla {tecla} ya la usa '{repetida.get('nombre')}', elige otra")
                return

            # Antes de tocar la acción: si una opción no es válida la guardada queda igual, no a medias
            # (otro salvarAcciones del dispositivo escribiría el cambio parcial al .md)
            opciones = None
            if self.opcionesEditar is not None:
                try:
                    opciones = self.leerOpciones(self.opcionesEditar, acción)
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
            dispositivoDestino.listaAcciones.sort(key=self.ordenTecla)
            dispositivoDestino.salvarAcciones()
            self.actualizarPestaña(dispositivoDestino)
            self.limpiarFormulario()
            self.ofrecerCrearFolder(guardada, dispositivoDestino)

        with ui.dialog() as self.dialogoPregunta, ui.card():
            self.textoPregunta = ui.label("")
            with ui.row():
                ui.button("Cancelar", on_click=self.dialogoPregunta.close).props("flat")
                self.botonPregunta = ui.button("", color=self.colorPeligro, on_click=self.confirmarPregunta).props("unelevated").mark("botonConfirmarPregunta")

        # Pasos de una macro como bloques; se llena al abrir con los pasos del editor YAML
        with ui.dialog() as self.dialogoPasos, ui.card().classes("w-full max-w-2xl"):
            miGui.encabezado(ui.label("Pasos de la macro").classes("text-lg"), 2)
            self.listaPasos = ui.column().classes("w-full gap-1")
            self.formularioPaso = ui.column().classes("w-full")
            with ui.row():
                ui.button("Agregar paso", icon="add", color=self.colorOscuro, on_click=lambda: self.editarPaso(None)).mark("botonAgregarPaso")
                ui.button("Cancelar", on_click=self.dialogoPasos.close).props("flat")
                ui.button("Listo", icon="check", color=self.colorOscuro, on_click=self.terminarPasos).mark("botonListoPasos")

        self.tituloFormulario = ui.label("").classes(f"text-{self.colorClaro} font-bold px-2").mark("tituloFormulario")
        with ui.scroll_area().classes("w-full").style("height: 75vh"):

            # Campos de dataAccion marcados con gui, la clave del dict es la clave en el .md
            self.editoresData = {propiedad.atributo: self.crearEditor(propiedad, f"editor-{propiedad.atributo}").props("clearable") for propiedad in dataAccion.propiedadesGui()}

            # Propiedades del folder: valores por defecto de los botones del folder actual
            with ui.dialog() as self.dialogoFolder, ui.card():
                miGui.encabezado(ui.label("Apariencia del folder").classes("text-lg"), 2)
                ui.label("Valores por defecto de los botones de este folder").classes("text-xs")
                self.editorFolderFondo = ui.color_input("Fondo", preview=True).classes("w-64").mark("editor-folder-fondo")
                self.editorFolderTamaño = ui.number("Tamaño máximo del título", min=1, precision=0).classes("w-64").mark("editor-folder-tamanno")
                # Solo dispositivos sin botones físicos (MQTT, GUI): se dibujan con esta cuadrícula
                with ui.row().classes("w-64 no-wrap") as self.filaFolderCuadricula:
                    self.editorFolderColumnas = ui.number("Columnas", min=1, precision=0).classes("flex-1").mark("editor-folder-columnas")
                    self.editorFolderFilas = ui.number("Filas", min=1, precision=0).classes("flex-1").mark("editor-folder-filas")
                ui.button("Guardar", color=self.colorOscuro, on_click=self.guardarPropiedadesFolder).mark("botonGuardarFolder")

            # entrar_folder a un folder donde el dispositivo no tiene archivo de acciones
            with ui.dialog() as self.dialogoCrearFolder, ui.card():
                self.textoCrearFolder = ui.label("")
                with ui.row():
                    ui.button("Cancelar", on_click=self.dialogoCrearFolder.close).props("flat")
                    ui.button("Crear y entrar", icon="create_new_folder", color=self.colorOscuro, on_click=self.crearFolderPendiente).mark("botonCrearFolder")

            # Se llena al abrir con las distribuciones disponibles
            with ui.dialog() as self.dialogoDistribucion, ui.card():
                self.listaDistribuciones = ui.column()

            # Apariencia del botón en un diálogo aparte para no llenar el formulario
            with ui.dialog() as self.dialogoBoton, ui.card():
                miGui.encabezado(ui.label("Apariencia del botón").classes("text-lg"), 2)
                with ui.row().classes("items-start"):
                    with ui.column().classes("w-64"):
                        self.editorTitulo = ui.input("Título", on_change=self.actualizarVistaPrevia).classes("w-full").props("clearable").mark("editor-titulo")
                        self.editorTituloMQTT = ui.input("Tópico MQTT del título", on_change=self.actualizarVistaPrevia).classes("w-full").props("clearable").mark("editor-titulo-mqtt")
                        self.editorTituloMQTT.props["hint"] = "El valor que llega reemplaza {} en el título, ej. {:.0f}%"
                        self.editorFondo = ui.color_input("Fondo", preview=True, on_change=self.actualizarVistaPrevia).classes("w-full").mark("editor-fondo")
                    self.vistaPrevia = ui.image().classes("w-24 h-24 rounded").props("fit=contain").mark("vistaPrevia")
                ui.button("Listo", color=self.colorOscuro, on_click=self.dialogoBoton.close).mark("botonListoBoton")
            ui.button("Editar apariencia", icon="palette", color=self.colorOscuro, on_click=self.abrirEditorApariencia).classes("w-full").mark("botonEditarBoton")

            self.listaNombreAcciones: list[str] = list()
            for clave in self.listaClasesAcciones.keys():
                claseAccion = self.listaClasesAcciones.get(clave)
                nombreAccion = claseAccion().nombre
                self.listaNombreAcciones.append(nombreAccion)

            self.editorAcción = ui.select(options=self.listaNombreAcciones, with_input=True, label="Acción", on_change=self.mostrarOpciones).classes("w-full").mark("editorAcción")
            self.editorDescripcion = ui.label("").classes(f"w-full bg-{self.colorTecla} p-2 text-white rounded-lg")
            self.editorDescripcion.visible = False
            self.editorPropiedades = ui.column().classes("w-full")
            self.editorOpción = ui.textarea(label="Opciones (solo lectura, se conservan al guardar)").classes("w-full").props("readonly").mark("editorOpción")
            self.editorOpción.visible = False

        with ui.row().classes("items-center gap-2"):
            # Ícono + (agregar) o disquete (guardar cambios); el tooltip dice cuál
            self.botonAgregar = ui.button(icon="add", color=self.colorOscuro, on_click=agregarAcción).props("rounded").mark("botonAgregar")
            with self.botonAgregar:
                self.tooltipAgregar = ui.tooltip()
            self.mostrarBotonGuardar(False)
            # Sueltos y no en button_group: con Ejecutar y Borrar ocultos el grupo deja Limpiar sin esquinas redondeadas
            # Ejecutar y Borrar solo se ven al editar una acción guardada
            self.botonEjecutar = ui.button(icon="play_arrow", color=self.colorOscuro, on_click=self.ejecutarAcciónEditada).props("rounded").mark("botonEjecutar")
            miGui.nombrar(self.botonEjecutar, "Ejecutar acción guardada")
            miGui.nombrar(ui.button(icon="clear_all", color=self.colorOscuro, on_click=lambda: self.siNoHayCambios(self.limpiarFormulario)).props("rounded").mark("botonLimpiar"), "Limpiar formulario")
            self.botonBorrar = ui.button(icon="delete", color=self.colorPeligro, on_click=self.borrarAcciónEditada).props("rounded").mark("botonBorrar")
            miGui.nombrar(self.botonBorrar, "Borrar acción")
            self.botonEjecutar.visible = self.botonBorrar.visible = False

    def mostrarBotonGuardar(self, editando: bool) -> None:
        """Agregar para una acción nueva, Guardar cambios al editar una guardada"""
        texto = "Guardar cambios" if editando else "Agregar acción"
        self.botonAgregar.icon = "save" if editando else "add"
        self.botonAgregar.props["aria-label"] = texto
        self.tooltipAgregar.text = texto

    def actualizarCabecera(self) -> None:
        """Muestra información del dispositivo rutas de la interfaz web"""
        if self.pestañas is None or self.folderLabel is None:
            return
        dispositivoActual = self.obtenerDispositivoSeleccionado()
        if dispositivoActual is not None:
            # El dispositivo ya se ve en la pestaña; "/" es el inicio del perfil
            folder = "/" + ("" if dispositivoActual.enFolderRaiz() else str(dispositivoActual.folderActual).strip("/"))
            # title: el folder se recorta con … si no cabe en la cabecera
            self.folderLabel.props["title"] = folder
            self.folderLabel.text = folder
        self.actualizarTituloFormulario()

    def cambiarModo(self, usar: bool) -> None:
        """Cambia entre Usar y Editar, lo recuerda para la próxima vez y redibuja los dispositivos"""
        self.modoUsar = usar
        SalvarValor(ARCHIVO_PREFERENCIAS, "modo_usar", usar)
        # Intercambiar es una herramienta de edición, no debe seguir activo en Usar
        self.teclaIntercambio.clear()
        self.acciónDuplicar.clear()
        self.aplicarModo()
        for dispositivoActual in self.listaDispositivos:
            self.actualizarPestaña(dispositivoActual)

    def aplicarModo(self) -> None:
        """Oculta el formulario en modo Usar; el formulario conserva lo que se estaba editando"""
        if self.splitter is None or self.contenedorFormulario is None:
            return
        self.contenedorFormulario.visible = not self.modoUsar
        self.splitter.value = 0 if self.modoUsar else 20
        if self.modoUsar:
            self.splitter.classes(add="modo-usar")
        else:
            self.splitter.classes(remove="modo-usar")

    def conectarTecla(self, boton: ui.element, acción: dataAccion, dispositivo: dispositivo) -> None:
        """Modo Usar: hundir la tecla presiona y levantarla suelta, igual que el aparato (ej. la acción Presiona)"""
        for evento in ("pointerdown", "keydown.enter", "keydown.space"):
            boton.on(evento, lambda: self.presionarTecla(acción, dispositivo))
        for evento in ("pointerup", "pointerleave", "pointercancel", "keyup.enter", "keyup.space"):
            boton.on(evento, lambda: self.soltarTecla(acción, dispositivo))

    def soltarTecla(self, acción: dataAccion, dispositivo: dispositivo) -> None:
        """Manda soltar solo si la tecla estaba presionada (pointerleave llega aunque no se haya presionado)"""
        if self.teclasPresionadas.pop(id(acción), None) is None:
            return
        self.buscarAccion(acción, self.estadoTecla.LIBERADA)

    def soltarTodas(self) -> None:
        for acción in list(self.teclasPresionadas.values()):
            self.soltarTecla(acción, None)

    def presionarTecla(self, acción: dataAccion, dispositivo: dispositivo) -> None:
        """Ejecuta la acción de una tecla en modo Usar y la muestra en la cabecera"""
        # Mantener Enter/Espacio repite keydown: se ejecuta una sola vez hasta soltar
        if id(acción) in self.teclasPresionadas:
            return
        self.teclasPresionadas[id(acción)] = acción
        nombre = acción.get("nombre") or str(acción.get("key"))
        try:
            self.buscarAccion(acción, self.estadoTecla.PRESIONADA)
        except Exception as error:
            self.teclasPresionadas.pop(id(acción), None)
            logger.warning(f"Ejecutar[Error] {dispositivo.nombre}[{acción.get('key')}] {error}")
            ui.notify(f"No se pudo ejecutar {nombre}: {error}", type="negative")
            return
        if self.ultimaLabel is not None:
            self.ultimaLabel.text = nombre
            self.ultimaFila.visible = True
            # Destello sin movimiento (vale también con reduced-motion): confirma que se ejecutó aunque el nombre no cambie
            ui.run_javascript(
                f"getHtmlElement({self.ultimaFila.id})?.animate([{{backgroundColor: 'rgba(94, 234, 212, 0.35)'}}, {{backgroundColor: 'transparent'}}], {{duration: 600, easing: 'ease-out'}})"
            )

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
                    editor = self.crearEditor(propiedad, f"opción-{nombre}")
                    tipoAnterior, valorAnterior = valoresAnteriores.get(nombre, (None, None))
                    if valorAnterior and tipoAnterior == editor.tipoEditor:
                        editor.value = valorAnterior
                    self.opcionesEditar[nombre] = editor
                    if propiedad.atributo == acciónTmp.atributoLista:
                        ui.button("Editar pasos", icon="view_list", color=self.colorOscuro, on_click=lambda e=editor: self.abrirPasos(e)).classes("w-full").mark("botonEditarPasos")
            return

        logger.warning(f"No hay opciones para: {accionSeleccionada}")

    def leerOpciones(self, editores: dict[str, ui.element], comandoAcción: str) -> dict | list:
        """Opciones con el tipo de cada propiedad; marca el campo y lanza ValueError si alguno no es válido"""
        opciones = dict()
        for editor in editores.values():
            propiedad: propiedadAccion = editor.propiedad
            try:
                valor = self.leerValor(editor)
                if valor is None and propiedad.obligatorio:
                    raise ValueError(f"Falta {propiedad.nombre}")
            except ValueError as error:
                self.avisarError(editor, str(error))
                raise
            if valor is not None:
                opciones[propiedad.atributo] = valor
        # Acciones como macro guardan sus opciones en el .md como lista
        atributoLista = getattr(self.obtenerAcciónOop(comandoAcción), "atributoLista", None)
        if atributoLista:
            return opciones.get(atributoLista, [])
        return opciones

    def cargarOpciones(self, editores: dict[str, ui.element], claseAcción: type[accion], opciones: dict | list) -> None:
        """Pone en los editores las opciones guardadas en el .md"""
        objetoClase = claseAcción()
        if isinstance(opciones, list) and objetoClase.atributoLista:
            opciones = {objetoClase.atributoLista: opciones}
        if isinstance(opciones, dict):
            for propiedad in objetoClase.listaPropiedades:
                if propiedad.atributo in opciones:
                    self.ponerValor(editores.get(propiedad.nombre), opciones[propiedad.atributo])

    def abrirPasos(self, editor: ui.element) -> None:
        """Abre los pasos del editor YAML de la macro como bloques"""
        try:
            pasos = self.leerValor(editor) or []
        except ValueError as error:
            self.avisarError(editor, str(error))
            return
        self.editorPasos = editor
        self.pasosMacro: list[dict] = copy.deepcopy(pasos)
        self.cerrarPaso()
        self.dibujarPasos()
        self.dialogoPasos.open()

    def terminarPasos(self) -> None:
        """Devuelve los pasos al editor YAML; se guardan en el .md con el resto del formulario"""
        self.ponerValor(self.editorPasos, self.pasosMacro)
        self.dialogoPasos.close()

    def dibujarPasos(self) -> None:
        """Un bloque por paso con su acción, un resumen de sus opciones y botones para ordenar, editar y borrar"""
        self.listaPasos.clear()
        with self.listaPasos:
            if not self.pasosMacro:
                ui.label("Sin pasos, agrega uno").classes("text-xs")
            for i, paso in enumerate(self.pasosMacro):
                comando = paso.get("accion")
                claseAcción = self.obtenerAcciónOop(comando)
                opciones = paso.get("opciones")
                resumen = yaml.safe_dump(opciones, allow_unicode=True, default_flow_style=True, width=1000).strip() if opciones else ""
                with ui.card().classes("w-full p-2").mark(f"paso-{i}"):
                    with ui.row().classes("w-full items-center no-wrap gap-2"):
                        ui.label(f"{i + 1}.").classes("font-bold")
                        with ui.column().classes("gap-0 grow min-w-0"):
                            ui.label(claseAcción().nombre if claseAcción else comando)
                            ui.label(resumen).classes("text-xs truncate w-full").tooltip(resumen)
                        with ui.button_group().props("flat"):
                            miGui.nombrar(ui.button(icon="arrow_upward", on_click=lambda i=i: self.moverPaso(i, -1)).props(f"flat {'disable' if i == 0 else ''}").mark(f"subirPaso-{i}"), "Subir paso")
                            miGui.nombrar(ui.button(icon="arrow_downward", on_click=lambda i=i: self.moverPaso(i, 1)).props(f"flat {'disable' if i == len(self.pasosMacro) - 1 else ''}").mark(f"bajarPaso-{i}"), "Bajar paso")
                            miGui.nombrar(ui.button(icon="edit", on_click=lambda i=i: self.editarPaso(i)).props("flat").mark(f"editarPaso-{i}"), "Editar paso")
                            miGui.nombrar(ui.button(icon="delete", color=self.colorPeligro, on_click=lambda i=i: self.borrarPaso(i)).props("flat").mark(f"borrarPaso-{i}"), "Borrar paso")

    def moverPaso(self, i: int, cambio: int) -> None:
        pasos = self.pasosMacro
        pasos[i], pasos[i + cambio] = pasos[i + cambio], pasos[i]
        self.cerrarPaso()
        self.dibujarPasos()

    def borrarPaso(self, i: int) -> None:
        self.pasosMacro.pop(i)
        self.cerrarPaso()
        self.dibujarPasos()

    def cerrarPaso(self) -> None:
        self.formularioPaso.clear()
        self.pasoEditando: int | None = None

    def editarPaso(self, i: int | None) -> None:
        """Formulario de un paso (None para uno nuevo): acción y sus opciones con los mismos editores del formulario"""
        self.cerrarPaso()
        self.pasoEditando = i
        paso = self.pasosMacro[i] if i is not None else {}
        comando = paso.get("accion")
        claseAcción = self.obtenerAcciónOop(comando)
        opciones = self.listaNombreAcciones + ([comando] if comando and claseAcción is None else [])
        with self.formularioPaso:
            ui.separator()
            ui.label(f"Paso {i + 1}" if i is not None else "Paso nuevo").classes("font-bold")
            # add-unique: se puede escribir el comando de una acción sin clase OOP (ej. obs_escena)
            self.editorAcciónPaso = (
                ui.select(opciones, with_input=True, new_value_mode="add-unique", label="Acción", value=claseAcción().nombre if claseAcción else comando, on_change=lambda: self.mostrarOpcionesPaso(None))
                .classes("w-full")
                .mark("editorAcciónPaso")
            )
            self.propiedadesPaso = ui.column().classes("w-full")
            with ui.row():
                ui.button("Guardar paso", icon="check", color=self.colorOscuro, on_click=self.guardarPaso).mark("botonGuardarPaso")
                ui.button("Cancelar", on_click=self.cerrarPaso).props("flat")
        self.mostrarOpcionesPaso(paso.get("opciones"))

    def comandoPaso(self) -> str | None:
        valor = self.editorAcciónPaso.value
        return self.comandoAcción(valor) or valor

    def mostrarOpcionesPaso(self, opciones: dict | list | None) -> None:
        """Editores de las opciones del paso; las acciones sin clase OOP se editan en YAML"""
        claseAcción = self.obtenerAcciónOop(self.comandoPaso())
        self.propiedadesPaso.clear()
        with self.propiedadesPaso:
            if claseAcción is None:
                propiedad = propiedadAccion("Opciones", "opciones", tipo=[dict, list])
                self.opcionesPaso = {propiedad.nombre: self.crearEditor(propiedad, "opción-paso-Opciones")}
                self.ponerValor(self.opcionesPaso[propiedad.nombre], opciones)
                return
            self.opcionesPaso = {propiedad.nombre: self.crearEditor(propiedad, f"opción-paso-{propiedad.nombre}") for propiedad in claseAcción().listaPropiedades}
        if opciones:
            self.cargarOpciones(self.opcionesPaso, claseAcción, opciones)

    def guardarPaso(self) -> None:
        comando = self.comandoPaso()
        if not comando:
            self.avisarError(self.editorAcciónPaso, "Falta elegir la acción")
            return
        try:
            opciones = self.leerOpciones(self.opcionesPaso, comando)
        except ValueError:
            return
        if self.obtenerAcciónOop(comando) is None and isinstance(opciones, dict):
            # Sin clase OOP: el único editor es el YAML de mostrarOpcionesPaso
            opciones = opciones.get("opciones")
        # Se copian las claves extra del paso (ej. macro_opciones)
        paso = dict(self.pasosMacro[self.pasoEditando]) if self.pasoEditando is not None else {}
        paso["accion"] = comando
        paso.pop("opciones", None)
        if opciones:
            paso["opciones"] = opciones
        if self.pasoEditando is None:
            self.pasosMacro.append(paso)
        else:
            self.pasosMacro[self.pasoEditando] = paso
        self.cerrarPaso()
        self.dibujarPasos()

    @staticmethod
    def tipoEditor(propiedad: propiedadAccion) -> str:
        """"bool", "numero", "yaml" (dict/list) o "texto" según los tipos que acepta la propiedad"""
        tipos = set(propiedad.tipo)
        if tipos == {bool}:
            return "bool"
        if tipos and tipos <= {int, float}:
            return "numero"
        if tipos and tipos <= {dict, list}:
            return "yaml"
        return "texto"

    @staticmethod
    def crearEditor(propiedad: propiedadAccion, marca: str) -> ui.element:
        """Crea el editor de una propiedad según su tipo: switch, número, YAML (dict/list) o texto; * si es obligatoria"""
        etiqueta = f"* {propiedad.nombre}" if propiedad.obligatorio else propiedad.nombre
        tipo = miGui.tipoEditor(propiedad)
        if tipo == "bool":
            editor = ui.switch(etiqueta, value=bool(propiedad.defecto))
            if propiedad.descripcion:
                editor.tooltip(propiedad.descripcion)
        else:
            if tipo == "numero":
                editor = ui.number(label=etiqueta, placeholder=propiedad.ejemplo, precision=None if float in propiedad.tipo else 0)
            elif tipo == "yaml" or propiedad.multilinea:
                editor = ui.textarea(label=etiqueta, placeholder=propiedad.ejemplo)
            else:
                editor = ui.input(label=etiqueta, placeholder=propiedad.ejemplo)
            # La ayuda queda visible debajo del campo, no en un aviso que desaparece
            ayuda = propiedad.descripcion or ""
            if tipo == "yaml":
                ayuda = f"{ayuda} (en YAML)".strip()
            if ayuda:
                editor.props["hint"] = ayuda
            editor.on_value_change(lambda _, e=editor: miGui.marcarError(e, None))
        editor.propiedad = propiedad
        editor.tipoEditor = tipo
        return editor.classes("w-full").mark(marca)

    @staticmethod
    def ponerValor(editor: ui.element, valor) -> None:
        """Muestra en el editor un valor guardado en el .md según el tipo del editor"""
        tipo = getattr(editor, "tipoEditor", "texto")
        if tipo == "yaml":
            editor.value = "" if valor in (None, "") else yaml.safe_dump(valor, allow_unicode=True, sort_keys=False)
        elif tipo == "numero":
            try:
                editor.value = None if valor in (None, "") else float(valor)
            except (TypeError, ValueError):
                # Ej: guardado como texto por una versión vieja de la GUI
                editor.value = None
                miGui.marcarError(editor, f"El valor guardado no es un número: {valor}")
        elif tipo == "bool":
            editor.value = bool(valor)
        else:
            editor.value = valor

    @staticmethod
    def leerValor(editor: ui.element):
        """Valor del editor con el tipo de su propiedad, None si quedó vacío; ValueError si no es válido"""
        propiedad: propiedadAccion = editor.propiedad
        valor = editor.value
        if editor.tipoEditor == "bool":
            # Solo se guarda si cambia el valor por defecto, para no llenar el .md
            return valor if propiedad.obligatorio or valor != bool(propiedad.defecto) else None
        if valor in ("", None):
            return None
        if editor.tipoEditor == "numero":
            return float(valor) if float in propiedad.tipo else int(valor)
        if editor.tipoEditor == "yaml":
            try:
                dato = yaml.safe_load(valor)
            except yaml.YAMLError as error:
                raise ValueError(f"{propiedad.nombre}: YAML con error ({getattr(error, 'problem', error)})")
            if not propiedad.mismoTipo(dato):
                tipos = " o ".join("lista" if t is list else "diccionario" for t in propiedad.tipo)
                raise ValueError(f"{propiedad.nombre}: debe ser {tipos} en YAML")
            return dato
        return valor

    @staticmethod
    def nombrar(elemento: ui.element, texto: str) -> ui.element:
        """Tooltip y nombre accesible (aria-label) para botones de solo ícono"""
        elemento.props["aria-label"] = texto
        return elemento.tooltip(texto)

    @staticmethod
    def encabezado(etiqueta: ui.label, nivel: int) -> ui.label:
        """Título que un lector de pantalla reconoce como encabezado (ui.label es un div)"""
        return etiqueta.props(f"role=heading aria-level={nivel}")

    @staticmethod
    def marcarError(editor: ui.element, mensaje: str | None) -> None:
        """Marca (o limpia con None) el error en el campo; sin validation de nicegui hay que usar las props de Quasar"""
        if getattr(editor, "tipoEditor", None) == "bool" or isinstance(editor, ui.switch):
            return
        # None y no False al limpiar: con error=False Quasar reserva espacio para el mensaje y el campo crece.
        # No quitar la prop, nicegui lee props["error"] al cambiar el valor y daría KeyError
        editor.props["error"] = mensaje is not None or None
        editor.props["error-message"] = mensaje
        editor.update()

    def avisarError(self, editor: ui.element, mensaje: str) -> None:
        """Marca el campo con el error y además lo avisa, por si el campo quedó fuera de la vista"""
        self.marcarError(editor, mensaje)
        ui.notify(mensaje, type="warning")
        logger.warning(f"Formulario[Error] {mensaje}")

    def limpiarErrores(self) -> None:
        for editor in [*self.editoresData.values(), self.editorAcción, *(self.opcionesEditar or {}).values()]:
            self.marcarError(editor, None)

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
        self.preguntar(f"Hay cambios sin guardar en {nombre}. ¿Descartarlos?", "Descartar", funcion)

    def preguntar(self, mensaje: str, textoBoton: str, funcion) -> None:
        """Diálogo de confirmación con mensaje variable (crearDialogoConfirmacion es para mensajes fijos)"""
        self.textoPregunta.text = mensaje
        self.botonPregunta.text = textoBoton
        self.funcionPregunta = funcion
        self.dialogoPregunta.open()

    def confirmarPregunta(self) -> None:
        self.dialogoPregunta.close()
        self.funcionPregunta()

    def actualizarTituloFormulario(self) -> None:
        """Dice arriba del formulario qué se está editando y en qué dispositivo se guardará"""
        if self.tituloFormulario is None:
            return
        destino = self.dispositivoEditar or (self.obtenerDispositivoSeleccionado() if self.pestañas else None)
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
        dispositivoActual = self.dispositivoEditar or (self.obtenerDispositivoSeleccionado() if self.pestañas else None)
        if dispositivoActual is None:
            return

        # Copia profunda: imagen_opciones es un dict y aplicarApariencia lo modifica, no debe tocar la acción guardada
        acción = copy.deepcopy(self.accionEditar) if self.accionEditar else dataAccion()
        acción.accion = self.comandoAcción(self.editorAcción.value) or acción.accion
        self.aplicarApariencia(acción)
        # En teclados cada tecla mide distinto, se usa la medida de la tecla editada
        tecla = str(self.editoresData["key"].value)
        teclaFisica = next((t for t in dispositivoActual.distribucionTeclas() or [] if t["key"] == tecla), None)
        tamaño = self.tamañoTecla(teclaFisica) if teclaFisica else dispositivoActual.tamañoBoton()
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
        self.probarAcción(acción)
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
        self.actualizarPestaña(dispositivo)

    def borrarAcciónEditada(self) -> None:
        """Borra la acción que está en el editor y lo limpia"""
        self.borrarConDeshacer(self.accionEditar, self.dispositivoEditar, antes=self.limpiarFormulario)

    def borrarConDeshacer(self, acción: dataAccion, dispositivo: dispositivo, antes=None) -> None:
        """Borra sin preguntar y muestra un aviso con Deshacer mientras dura"""
        if antes is not None:
            antes()
        posición = dispositivo.listaAcciones.index(acción)
        self.contadorBorrados += 1
        idBorrado = self.contadorBorrados
        self.borrados[idBorrado] = (acción, dispositivo, dispositivo.folderActual, posición)
        ui.notification(
            f"{acción.get('nombre')} borrada de {dispositivo.nombre}",
            timeout=10,
            close_button="Cerrar",
            on_dismiss=lambda: self.borrados.pop(idBorrado, None),
            actions=[{"label": "Deshacer", "color": "white", ":handler": f"() => emitEvent('deshacerBorrar', {idBorrado})"}],
        )
        # Después del aviso: borrar redibuja la lista y elimina el botón desde el que se llamó
        self.borrarAcción(acción, dispositivo)

    def deshacerBorrar(self, idBorrado: int) -> None:
        """Vuelve a poner la acción borrada en su lugar y guarda el archivo"""
        borrado = self.borrados.pop(idBorrado, None)
        if borrado is None:
            return
        acción, dispositivo, folder, posición = borrado
        nombre = acción.get("nombre")
        # ponytail: listaAcciones es la del folder abierto; si el dispositivo navegó no se puede restaurar sin reabrir el otro archivo
        if dispositivo.folderActual != folder:
            ui.notify(f"No se pudo deshacer: {dispositivo.nombre} ya no está en el folder {folder}", type="warning")
            return
        repetida = self.teclaRepetida(dispositivo.listaAcciones, acción.get("key"), None)
        if repetida is not None:
            ui.notify(f"No se pudo deshacer: la tecla {acción.get('key')} ya la usa '{repetida.get('nombre')}'", type="warning")
            return
        dispositivo.listaAcciones.insert(posición, acción)
        dispositivo.salvarAcciones()
        self.actualizarPestaña(dispositivo)
        ui.notify(f"{nombre} restaurada en {dispositivo.nombre}", type="positive")

    def crearPestañas(self) -> None:
        """Crea las pestañas de los dispositivos"""
        if self.pestañas is None or self.paneles is None:
            logger.warning("No hay pestañas o paneles para mostrar")
            return

        self.listaDispositivos.sort(key=lambda x: x.nivelOrdenar, reverse=True)

        with self.pestañas:
            for dispositivoActual in self.listaDispositivos:
                nombreDispositivo: str = dispositivoActual.nombre
                # Cambiar de pestaña no limpia el formulario: la edición sigue ligada a su dispositivo (ver tituloFormulario)
                dispositivoActual.pestaña = ui.tab(nombreDispositivo)

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

            if claseAcción is not None:
                self.cargarOpciones(self.opcionesEditar, claseAcción, opcionesActuales)
            else:
                # Sin editor para estas opciones (ej. pasos de una macro): se muestran y se guardan sin cambios
                self.editorOpción.visible = True
                self.editorOpción.value = yaml.safe_dump(opcionesActuales, allow_unicode=True, sort_keys=False)
        self.recordarFormulario()

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
            ui.notify(f"{nombre} {'activado' if valor else 'desactivado'}. Reinicia ElGarrobo para aplicarlo")

        miGui.encabezado(ui.label(titulo).classes("text-h5 p-4"), 2)
        ui.label("Los cambios se aplican al reiniciar ElGarrobo (menú → Reiniciar)").classes(f"text-caption px-4 text-{self.colorClaro}")
        with ui.column().classes("p-4 gap-2 w-full"):
            for clase in listaClases:
                activo = configuracion.get(clase.modulo, False)
                with ui.row().classes(f"items-center w-full border-b border-{self.colorOscuro} pb-2"):
                    interruptor = ui.switch(value=activo, on_change=lambda e, c=clase: cambiarEstado(c.modulo, e.value, c.nombre))
                    interruptor.props["aria-label"] = f"Activar {clase.nombre}"
                    with ui.column().classes("gap-0"):
                        ui.label(clase.nombre).classes("font-bold")
                        ui.label(clase.descripcion).classes("text-caption")
                # Los módulos también tienen archivoConfiguracion, pero no es una lista de aparatos
                if issubclass(clase, dispositivo) and clase.archivoConfiguracion:
                    self.mostrarAparatos(clase)

    def mostrarAparatos(self, clase: type[dispositivo]) -> None:
        """Lista los aparatos de un tipo (ej. teclados.md) con un desplegable para editar nombre y orden"""
        archivo = clase.archivoConfiguracion
        aparatos = ObtenerArchivo(archivo) or []

        def guardar(data: dict, nombre: ui.input, orden: ui.number, internos: list, desplegable: ui.expansion) -> None:
            nombreNuevo = (nombre.value or "").strip()
            error = None
            # elGarrobo busca dispositivos por nombre sin importar mayúsculas (ej. entrar_folder con 'dispositivo')
            if any(otro is not data and str(otro.get("nombre")).lower() == nombreNuevo.lower() for otro in aparatos):
                error = f"Ya existe {nombreNuevo}"
            self.marcarError(nombre, "El nombre no puede quedar vacío" if not nombreNuevo else error)
            vacíos = [editor for _, editor in internos if not (editor.value or "").strip()]
            for _, editor in internos:
                self.marcarError(editor, "Falta el nombre" if editor in vacíos else None)
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
                    desplegable.classes(f"w-full border border-{self.colorOscuro} rounded")
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
                        color=self.colorOscuro,
                        on_click=lambda d=data, n=nombre, o=orden, i=editoresInternos, e=desplegable: guardar(
                            d, n, o, i, e
                        ),
                    ).classes("m-2")

    def crearDialogoConfirmacion(self, mensaje: str, textoBoton: str, accionConfirmada) -> ui.dialog:
        """Crea (sin abrir) un diálogo de confirmación para una acción crítica.

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

                ui.button(textoBoton, color=self.colorPeligro, on_click=confirmar).props("unelevated")
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

    def estructura(self, conModo: bool = False):
        """Estructura de la interfaz, cabecera y pie de página

        Args:
            conModo (bool): Página de acciones: muestra dispositivo/folder, última acción y el interruptor Usar/Editar
        """
        ui.add_css(CSS_BOTONERA)
        ui.colors(**COLORES_QUASAR)
        with ui.header(elevated=True) as cabecera:
            cabecera.classes(f"bg-{self.colorOscuro} items-center justify-between gap-0")
            cabecera.style("padding: 1px")
            miGui.encabezado(ui.label("ElGarrobo").classes("text-h5 px-4 sm:px-8"), 1)
            if conModo and self.pestañas is not None:
                cabecera.classes("cabecera-grilla")
                self.pestañas.move(cabecera)
            # Lado derecho en un solo bloque: en la grilla ocupa la tercera columna; el folder se recorta si no cabe
            with ui.row().classes("items-center justify-end gap-6 no-wrap min-w-0"):
                if conModo:
                    with ui.row().classes("items-center gap-6 no-wrap min-w-0 max-sm:hidden"):
                        with ui.row().classes("items-center gap-1 no-wrap min-w-0"):
                            ui.icon("folder", color=self.colorClaro)
                            self.folderLabel = ui.label("").classes(f"text-{self.colorClaro} truncate").mark("cabecera-folder")
                        with ui.row().classes("items-center gap-1 rounded px-2 no-wrap min-w-0") as self.ultimaFila:
                            ui.icon("play_arrow", color=self.colorClaro)
                            self.ultimaLabel = ui.label("").classes("truncate").mark("ultimaAcción")
                        self.ultimaFila.visible = False
                dialogoReiniciar = self.crearDialogoConfirmacion("¿Reiniciar ElGarrobo? Las teclas no responden mientras arranca.", "Reiniciar", self.reiniciar)
                dialogoSalir = self.crearDialogoConfirmacion("¿Cerrar ElGarrobo? Las teclas y esta página dejan de funcionar hasta que lo vuelvas a abrir.", "Salir", self.salir)
                with ui.dialog() as dialogoAcercaDe, ui.card():
                    ui.label("ElGarrobo").classes("text-h6")
                    ui.label("Creado por ChepeCarlos")
                    with ui.row():
                        ui.link("YouTube", "https://www.youtube.com/@chepecarlo", new_tab=True).classes(f"text-{self.colorClaro}")
                        ui.link("TikTok", "https://www.tiktok.com/@chepecarlo", new_tab=True).classes(f"text-{self.colorClaro}")
                    ui.button("Cerrar", on_click=dialogoAcercaDe.close).props("flat")
                with ui.row().classes("items-center gap-2 no-wrap"):
                    if conModo:
                        modo = ui.toggle({True: "Usar", False: "Editar"}, value=self.modoUsar, on_change=lambda e: self.cambiarModo(e.value))
                        modo.classes("modo-toggle").props("rounded unelevated no-caps toggle-text-color=black text-color=white").props(f"toggle-color={self.colorSeleccion} color={self.colorInterruptor}").mark("modo")
                    with ui.button(icon="menu").props("flat color=white aria-label=Menú").classes("px-8"):
                        with ui.menu():
                            ui.menu_item("Acciones", on_click=lambda: ui.navigate.to("/")).mark("menu-Acciones")
                            ui.menu_item("Módulos", on_click=lambda: ui.navigate.to("/modulos")).mark("menu-Módulos")
                            ui.menu_item("Dispositivos", on_click=lambda: ui.navigate.to("/dispositivos")).mark("menu-Dispositivos")
                            ui.menu_item("Acerca de", on_click=dialogoAcercaDe.open).mark("menu-AcercaDe")
                            ui.separator()
                            ui.menu_item("Reiniciar", on_click=dialogoReiniciar.open).mark("menu-Reiniciar")
                            ui.menu_item("Salir", on_click=dialogoSalir.open).mark("menu-Salir")


    def seConectaGUI(self, client=None):
        """
        Inicia la interfaz web.
        """
        from elGarrobo.accionesOOP.accionListaCheckBox import accionListaCheckBox

        if client is not None:
            accionListaCheckBox.registrarCliente(client)
            logger.info(f"Conectando NiceGUI - cliente {client.id}")
        else:
            logger.info("Conectando NiceGUI")

    def seDesconectaGUI(self, client=None):
        """
        Desconecta la interfaz web.
        """
        if client is not None:
            logger.info(f"Desconectando NiceGUI - cliente {client.id}")
        else:
            logger.info("Desconectando NiceGUI")
        # app.shutdown()

    def conectar(self):

        logger.info("Iniciando NiceGUI")
        # Aquí y no en __init__: los tests crean miGui sin conectar y no deben depender de la config del usuario
        self.modoUsar = bool((leerData(ARCHIVO_PREFERENCIAS) or {}).get("modo_usar", False))

        app.on_connect(self.seConectaGUI)
        app.on_disconnect(self.seDesconectaGUI)

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
            logger.error(f"GUI[Error] No se pudo iniciar la GUI - {error}")

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

    def actualizarPestaña(self, dispositivo: dispositivo) -> None:
        """Actualiza las acciones de la pestaña del dispositivo

        Args:
            dispositivo (dispositivo): dispositivo a actualizar la pestaña
        """
        nombre = dispositivo.nombre

        if self.paneles is None:
            logger.warning("No hay paneles")
            return

        if dispositivo.panel is None:
            logger.warning(f"dispositivo {nombre} sin panel")
            return

        with self.paneles:
            dispositivo.panel.clear()
            # Las teclas y herramientas viejas ya no existen; dibujarCuadricula y barraHerramientas las vuelven a guardar
            self.teclasDibujadas.pop(nombre, None)
            self.herramientasModo.pop(nombre, None)
            with dispositivo.panel:
                acciones = dispositivo.listaAcciones
                cuadricula = dispositivo.gruposBotones() is not None or dispositivo.distribucionTeclas() is not None
                usar = self.modoUsar
                self.barraHerramientas(dispositivo, cuadricula)

                with ui.scroll_area() as areaScroll:
                    areaScroll.classes("w-full" if usar else f"w-full border-2 border-{self.colorBorde}")
                    # Alto disponible: 100vh - cabecera con pestañas - padding de página y panel (64px) - borde (2px) - barra y su separación (52 + 16px)
                    areaScroll.style("height: calc(100vh - var(--alto-cabecera) - 134px)")

                    if acciones is None:
                        ui.label(f"{nombre} no tiene acciones en este folder")
                        return

                    # container-type: las teclas del StreamDeck se miden con cqw contra este ancho, no el de la ventana
                    with ui.element("div").classes(f"w-full {self.claseNavegación(dispositivo)}").style("container-type: inline-size"):
                        if cuadricula and (usar or nombre not in self.dispositivosEnLista):
                            self.dibujarCuadricula(acciones, dispositivo)
                        elif usar:
                            self.dibujarBotonera(acciones, dispositivo)
                        else:
                            self.dibujarAcciones(acciones, dispositivo)

            self.actualizarCabecera()

        if hasattr(dispositivo, "actualizarIconos"):
            dispositivo.actualizarIconos()

    def claseNavegación(self, dispositivo: dispositivo) -> str:
        """Clase CSS de entrada si cambió el folder o la página desde el último dibujo; editar o cambiar de modo no anima"""
        página = dispositivo.paginaActual() if hasattr(dispositivo, "paginaActual") else 1
        actual = (Path(str(dispositivo.folderActual or "").strip("/")), página)
        anterior = self.últimaVista.get(dispositivo.nombre)
        self.últimaVista[dispositivo.nombre] = actual
        if anterior is None or anterior == actual:
            return ""
        if actual[0] == anterior[0]:
            regresa = página < anterior[1]
        else:
            regresa = len(actual[0].parts) < len(anterior[0].parts)
        return "navega-sale" if regresa else "navega-entra"

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
        usar = self.modoUsar
        # En Usar las teclas no llevan etiqueta: la vista previa es lo que muestra el aparato

        teclasDibujadas = self.teclasDibujadas[nombre] = {}

        def alClick(tecla, acción):
            if usar:
                # En Usar ejecutan los eventos de conectarTecla; la tecla vacía no hace nada
                return None
            # El modo (intercambiar, duplicar o editar) se mira al hacer click: cambiarlo no redibuja las teclas
            return lambda: self.clickTecla(dispositivo, tecla, acción)

        def marcar(boton, tecla) -> None:
            acción = accionesPorTecla.get(str(tecla))
            if usar and acción is not None:
                self.conectarTecla(boton, acción, dispositivo)
            if not usar:
                teclasDibujadas[str(tecla)] = (boton, acción)
                self.marcarTecla(dispositivo, tecla, boton, acción)
            boton.mark(f"tecla-{nombre}-{tecla}")

        if distribucion:
            # Teclado: botones con posición libre en unidades de tecla, dibujados como el StreamDeck pero a la medida de cada tecla
            unidad = self.unidadTecla
            dibujo = dispositivo.dibujo()
            ancho, alto = self.medidaDistribucion(distribucion)
            # El teclado crece hasta llenar el ancho y alto del área (sin pasar de unidad px por tecla); posiciones en % del teclado
            relleno = "3rem" if usar else "1rem"
            medidaTeclado = f"width: min(100% - {relleno}, {ancho * unidad}px, (100vh - var(--alto-cabecera) - 172px) * {ancho / alto:.4f})"
            with ui.element("div").classes(f"mx-auto {'carcasa box-content' if usar else 'm-2'}").style(medidaTeclado):
                with ui.element("div").classes("relative w-full").style(f"aspect-ratio: {ancho} / {alto}"):
                    for teclaFisica in distribucion:
                        tecla = teclaFisica["key"]
                        acción = accionesPorTecla.get(tecla)
                        etiqueta = teclaFisica.get("etiqueta") or tecla.removeprefix("KEY_")
                        x, y = teclaFisica.get("x", 0), teclaFisica.get("y", 0)
                        tamaño = self.tamañoTecla(teclaFisica)
                        imagen = None
                        if acción is not None:
                            try:
                                imagen = dibujo.dibujarAnimado(acción, tamaño) or dibujo.dibujar(acción, tamaño, conGif=True)
                            except Exception as error:
                                logger.warning(f"Vista previa[Error] {nombre}[{tecla}] {error}")
                        if imagen is not None:
                            boton = ui.button(on_click=alClick(tecla, acción)).props("flat padding=0")
                            boton.props["aria-label"] = acción.get("nombre") or tecla
                            with boton:
                                ui.image(urlVista(imagen)).classes("w-full h-full rounded")
                        else:
                            boton = ui.button(acción.get("nombre") if acción else etiqueta, color=self.colorTecla if acción else self.colorTeclaVacia, on_click=alClick(tecla, acción))
                            boton.props("dense no-caps").classes("text-xs leading-tight")
                        boton.classes("absolute overflow-hidden rounded tecla-viva")
                        boton.set_enabled(not (usar and acción is None))
                        w, h = teclaFisica.get("w", 1), teclaFisica.get("h", 1)
                        boton.style(f"left: {x / ancho:.4%}; top: {y / alto:.4%}; width: calc({w / ancho:.4%} - 4px); height: calc({h / alto:.4%} - 4px); min-width: 0; min-height: 0")
                        boton.tooltip(f"{etiqueta} ({tecla})" + (f": {acción.get('nombre')}" if acción else ""))
                        marcar(boton, tecla)
            # Acciones en teclas que no están dibujadas (capa Fn, teclas de otro modelo) para que no queden escondidas
            self.dibujarOtrasTeclas(accionesPorTecla, {t["key"] for t in distribucion}, alClick, marcar)

        if not grupos:
            return

        # La tecla se ajusta para que todos los grupos quepan lado a lado en el ancho y el alto del área (ej. celular)
        # ponytail: los rem de separación son aproximados (padding, gaps, etiquetas); ajustar si sobra o falta espacio
        columnas = sum(grupo.columnas for grupo in grupos)
        filas = max(grupo.filas for grupo in grupos)
        separación = 0.75 if usar else 0.5
        extraAncho = (4 if usar else 1) + 2 * (len(grupos) - 1) + separación * (columnas - len(grupos))
        extraAlto = (3 if usar else 1) + (1.5 if len(grupos) > 1 else 0)
        porFila = separación + (0 if usar else 1.5)
        altoLibre = f"100vh - var(--alto-cabecera) - 88px - {extraAlto}rem"
        lado = f"min((100cqw - {extraAncho}rem) / {columnas}, ({altoLibre}) / {filas} - {porFila}rem)"
        medidaTecla = f"width: clamp(3rem, {lado}, {'9rem' if usar else '8rem'}); height: auto; aspect-ratio: 1"

        with ui.row().classes(f"items-start gap-8 no-wrap {'carcasa w-fit mx-auto max-sm:p-3' if usar else 'p-2 justify-center'}"):
            for grupo in grupos:
                dibujante = grupo.dibujante
                dibujo = dibujante.dibujo()
                tamaño = dibujante.tamañoBoton()
                # El aparato ya está rotado frente al usuario, el ícono se muestra derecho
                rotarAparato = getattr(dibujante, "rotar", 0)

                with ui.column().classes("items-center"):
                    if len(grupos) > 1:
                        ui.label(grupo.nombre).classes("font-bold")
                    with ui.grid(columns=grupo.columnas).classes("gap-3 max-sm:gap-2" if usar else "gap-2"):
                        for indice in range(grupo.filas * grupo.columnas):
                            tecla = grupo.primeraTecla + indice
                            acción = accionesPorTecla.get(str(tecla))
                            imagen = None
                            if acción is not None:
                                try:
                                    imagen = dibujo.dibujarAnimado(
                                        acción, tamaño, compensarRotar=rotarAparato, fps=getattr(dibujante, "fps", None)
                                    ) or dibujo.dibujar(acción, tamaño, conGif=True, compensarRotar=rotarAparato)
                                except Exception as error:
                                    logger.warning(f"Vista previa[Error] {nombre}[{tecla}] {error}")

                            with ui.column().classes("items-center gap-1"):
                                if imagen is not None:
                                    # Botón y no imagen suelta: se enfoca con Tab y se activa con Enter/Espacio
                                    boton = ui.button(on_click=alClick(tecla, acción)).props("flat padding=0").classes("rounded tecla-viva").style(medidaTecla)
                                    boton.props["aria-label"] = acción.get("nombre") or str(tecla)
                                    with boton:
                                        ui.image(urlVista(imagen)).classes("w-full h-full rounded")
                                    boton.tooltip(acción.get("nombre") or str(tecla))
                                elif usar:
                                    boton = ui.element("div").classes(f"rounded bg-{self.colorTeclaApagada}").style(medidaTecla)
                                else:
                                    boton = ui.button(icon="add", color=self.colorTeclaVacia, on_click=alClick(tecla, acción)).style(medidaTecla)
                                    boton.props["aria-label"] = f"Agregar acción en la tecla {tecla}"
                                marcar(boton, tecla)
                                if not usar:
                                    etiqueta = f"{tecla}: {acción.get('nombre')}" if acción is not None else str(tecla)
                                    ui.label(etiqueta).classes("text-xs truncate text-center").style(medidaTecla.split(";")[0]).tooltip(etiqueta)
                    if isinstance(dibujante, MiStreamDeckPlus):
                        self.dibujarControlesPlus(dibujante, accionesPorTecla, alClick, marcar)
        if miGui.usaCuadriculaFolder(dispositivo):
            # Teclas de texto (MQTT) o fuera de la cuadrícula del folder
            celdas = sum(grupo.filas * grupo.columnas for grupo in grupos)
            self.dibujarOtrasTeclas(accionesPorTecla, {str(tecla) for tecla in range(1, celdas + 1)}, alClick, marcar)

    def dibujarOtrasTeclas(self, accionesPorTecla: dict, dibujadas: set[str], alClick, marcar) -> None:
        """Fila con las acciones cuyas teclas no se dibujaron, para que no queden escondidas"""
        otras = [tecla for tecla in accionesPorTecla if tecla not in dibujadas | {"propiedad_folder"}]
        if not otras:
            return
        ui.label("Otras teclas").classes("font-bold px-2")
        with ui.row().classes("gap-1 px-2"):
            for tecla in otras:
                acción = accionesPorTecla[tecla]
                boton = ui.button(acción.get("nombre"), color=self.colorTecla, on_click=alClick(tecla, acción)).props("dense no-caps")
                boton.classes("text-xs tecla-viva").tooltip(tecla)
                marcar(boton, tecla)

    @staticmethod
    def usaCuadriculaFolder(aparato: dispositivo) -> bool:
        """Dispositivos sin botones físicos (MQTT, GUI): su cuadrícula sale de la propiedad_folder"""
        # Los teclados no: eligen una distribución
        return type(aparato).gruposBotones is dispositivo.gruposBotones and not hasattr(aparato, "cambiarDistribucion")

    def barraHerramientas(self, dispositivo: dispositivo, cuadricula: bool) -> None:
        """Fila sobre el área del dispositivo: subir folder, páginas, herramientas de edición y la vista Cuadrícula/Lista"""
        nombre = dispositivo.nombre
        usar = self.modoUsar
        enLista = cuadricula and nombre in self.dispositivosEnLista
        with ui.row().classes("items-center p-2 w-full gap-2"):
            subir = ui.button(icon="arrow_upward", color=self.colorBotones, on_click=lambda: self.subirFolder(dispositivo)).mark(f"subirFolder-{nombre}")
            miGui.nombrar(subir, "Subir al folder anterior")
            subir.set_enabled(not dispositivo.enFolderRaiz())
            if hasattr(dispositivo, "siguientePagina") and cuadricula and not enLista:
                anterior = ui.button(icon="chevron_left", color=self.colorBotones, on_click=lambda: self.cambiarPagina(dispositivo, dispositivo.anteriorPagina)).mark(f"paginaAnterior-{nombre}")
                miGui.nombrar(anterior, "Página anterior").set_enabled(dispositivo.puedeAnteriorPagina())
                ui.label(f"Página {dispositivo.paginaActual()}").mark(f"pagina-{nombre}")
                siguiente = ui.button(icon="chevron_right", color=self.colorBotones, on_click=lambda: self.cambiarPagina(dispositivo, lambda: dispositivo.siguientePagina(not usar))).mark(f"paginaSiguiente-{nombre}")
                miGui.nombrar(siguiente, "Página siguiente").set_enabled(dispositivo.puedeSiguientePagina(not usar))
            if usar:
                return
            ui.space()
            if cuadricula and not enLista:
                intercambiar = ui.button(icon="swap_horiz", color=self.colorBotones, on_click=lambda: self.cambiarModoIntercambio(dispositivo)).mark(f"intercambiar-{nombre}")
                miGui.nombrar(intercambiar, "Intercambiar teclas")
                duplicar = ui.button(icon="content_copy", color=self.colorBotones, on_click=lambda: self.cambiarModoDuplicar(dispositivo)).mark(f"duplicar-{nombre}")
                miGui.nombrar(duplicar, "Duplicar acción")
                self.herramientasModo[nombre] = {"intercambiar": intercambiar, "duplicar": duplicar}
                self.pintarHerramientas(dispositivo)
            apariencia = ui.button(icon="folder_special", color=self.colorBotones, on_click=lambda: self.abrirPropiedadesFolder(dispositivo)).mark(f"propiedadesFolder-{nombre}")
            miGui.nombrar(apariencia, "Apariencia del folder")
            if hasattr(dispositivo, "cambiarDistribucion"):
                self.botonDistribucion(dispositivo)
            if cuadricula:
                with ui.button_group().props("unelevated rounded"):
                    for lista, icono, texto in ((False, "grid_view", "Vista cuadrícula"), (True, "view_list", "Vista lista")):
                        activo = lista == enLista
                        vista = ui.button(icon=icono, on_click=lambda lista=lista: self.cambiarVista(dispositivo, lista))
                        vista.props(f"color={self.colorSeleccion if activo else self.colorInterruptor} text-color={'black' if activo else 'white'}")
                        vista.props["aria-pressed"] = activo
                        miGui.nombrar(vista, texto).mark(f"vista-{'lista' if lista else 'cuadricula'}-{nombre}")

    def dibujarControlesPlus(self, plus, accionesPorTecla: dict, alClick, marcar) -> None:
        """Pantalla táctil y perillas del StreamDeck Plus, debajo de sus teclas y del mismo ancho

        La pantalla se divide en tantas zonas como acciones touchscreen_N haya, igual que el aparato;
        en Editar se agrega una zona vacía al final para crear la siguiente.
        """
        usar = self.modoUsar
        nombre = plus.nombre

        def control(tecla: str, descripción: str, icono: str | None = None, texto: str | None = None) -> ui.button:
            acción = accionesPorTecla.get(tecla)
            boton = ui.button(texto, icon=icono, color=self.colorTecla if acción else self.colorTeclaVacia, on_click=alClick(tecla, acción))
            boton.props("dense no-caps").classes("tecla-viva")
            # Sin acción en Usar se ve apagado: ese control del aparato no hace nada
            boton.set_enabled(not (usar and acción is None))
            nombreAcción = acción.get("nombre") if acción else "sin acción"
            boton.props["aria-label"] = f"{descripción}: {nombreAcción}"
            boton.tooltip(f"{descripción} ({tecla}): {nombreAcción}")
            marcar(boton, tecla)
            return boton

        zonas = sorted(
            (tecla for tecla in accionesPorTecla if tecla.startswith("touchscreen_") and tecla.removeprefix("touchscreen_").isdigit()),
            key=lambda tecla: int(tecla.removeprefix("touchscreen_")),
        )
        if not usar:
            siguiente = int(zonas[-1].removeprefix("touchscreen_")) + 1 if zonas else 1
            zonas.append(f"touchscreen_{siguiente}")
        dibujo = plus.dibujo()
        tamañoZona = (plus.anchoBarra // max(len(zonas), 1), plus.altoBarra)

        # width 0 + min-width 100%: toma el ancho de las teclas sin ensancharlas (las imágenes no empujan la columna)
        with ui.column().classes("gap-1 mt-2").style("width: 0; min-width: 100%").mark(f"pantallaTactil-{nombre}"):
            if not usar:
                ui.label("Pantalla táctil").classes("text-xs")
            with ui.row().classes("w-full no-wrap gap-1"):
                if not zonas:
                    # Usar sin acciones: el aparato deja la pantalla negra
                    ui.element("div").classes(f"w-full rounded bg-{self.colorTeclaApagada}").style(f"aspect-ratio: {plus.anchoBarra} / {plus.altoBarra}")
                for posición, tecla in enumerate(zonas, start=1):
                    acción = accionesPorTecla.get(tecla)
                    with ui.column().classes("flex-1 min-w-0 gap-1"):
                        imagen = None
                        if acción is not None:
                            try:
                                imagen = dibujo.dibujar(acción, tamañoZona, conGif=True)  # el touchscreen del Plus no anima gifs
                            except Exception as error:
                                logger.warning(f"Vista previa[Error] {nombre}[{tecla}] {error}")
                        if imagen is not None:
                            boton = ui.button(on_click=alClick(tecla, acción)).props("flat padding=0").classes("w-full rounded tecla-viva")
                            with boton:
                                ui.image(urlVista(imagen)).classes("w-full h-full rounded")
                            boton.props["aria-label"] = f"Zona {posición} de la pantalla: {acción.get('nombre')}"
                            boton.tooltip(f"Zona {posición} ({tecla}): {acción.get('nombre')}")
                            marcar(boton, tecla)
                        else:
                            boton = control(tecla, f"Zona {posición} de la pantalla", icono=None if acción else "add", texto=acción.get("nombre") if acción else None)
                            boton.classes("w-full")
                        boton.style(f"aspect-ratio: {tamañoZona[0]} / {tamañoZona[1]}; min-height: 0")
                        # El aparato busca el deslizar por la posición de la zona, no por el número de touchscreen_N
                        with ui.row().classes("w-full no-wrap gap-1 justify-between"):
                            control(f"deslizar_izquierda_{posición}", f"Deslizar a la izquierda en la zona {posición}", icono="west").props("flat size=sm")
                            control(f"deslizar_derecha_{posición}", f"Deslizar a la derecha en la zona {posición}", icono="east").props("flat size=sm")

            if not usar:
                ui.label("Perillas").classes("text-xs mt-2")
            # En celular las cuatro perillas no caben en el ancho de las teclas: pasan a dos filas
            with ui.row().classes("w-full justify-around gap-x-1 gap-y-2 mt-1").mark(f"perillas-{nombre}"):
                for dial in range(1, (plus.cantidadDial or plus.cantidadDialDefecto) + 1):
                    with ui.column().classes("items-center gap-1 min-w-0"):
                        with ui.row().classes("items-center no-wrap gap-0"):
                            control(f"dial_izquierdo_{dial}", f"Girar a la izquierda la perilla {dial}", icono="rotate_left").props("flat round dense")
                            control(f"dial_{dial}", f"Presionar la perilla {dial}", icono="radio_button_checked").props("round")
                            control(f"dial_derecho_{dial}", f"Girar a la derecha la perilla {dial}", icono="rotate_right").props("flat round dense")
                        if not usar:
                            presionar = accionesPorTecla.get(f"dial_{dial}")
                            etiqueta = f"{dial}: {presionar.get('nombre')}" if presionar else str(dial)
                            ui.label(etiqueta).classes("text-xs truncate text-center max-w-full").tooltip(etiqueta)

    unidadTecla = 112
    "Pixeles de una tecla de 1x1 en la distribución del teclado: resolución del dibujo y tamaño máximo en pantalla"

    @classmethod
    def tamañoTecla(cls, teclaFisica: dict) -> tuple[int, int]:
        """Ancho y alto en pixeles de una tecla de la distribución, dejando 4px de separación"""
        return (int(teclaFisica.get("w", 1) * cls.unidadTecla) - 4, int(teclaFisica.get("h", 1) * cls.unidadTecla) - 4)

    @staticmethod
    def medidaDistribucion(distribucion: list[dict]) -> tuple[float, float]:
        """Ancho y alto del teclado en unidades de tecla"""
        ancho = max(t.get("x", 0) + t.get("w", 1) for t in distribucion)
        alto = max(t.get("y", 0) + t.get("h", 1) for t in distribucion)
        return ancho, alto

    def botonDistribucion(self, dispositivo: dispositivo) -> None:
        distribucion = ui.button(icon="keyboard", color=self.colorBotones, on_click=lambda: self.abrirDistribuciones(dispositivo)).mark(f"distribucion-{dispositivo.nombre}")
        miGui.nombrar(distribucion, "Distribución del teclado")

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
            miGui.encabezado(ui.label(f"Distribución de {dispositivo.nombre}").classes("text-lg"), 2)
            ui.label(f"Agrega las tuyas (JSON de keyboard-layout-editor.com) en {folderDistribucionesUsuario()}").classes("text-xs")
            for nombreDistribucion in [None, *distribucionesDisponibles()]:
                actual = nombreDistribucion == dispositivo.distribucion
                with ui.card().classes(f"w-full cursor-pointer opcion-distribucion {f'border-2 border-{self.colorActivo}' if actual else ''}") as tarjeta:
                    tarjeta.props(f"tabindex=0 role=button aria-pressed={str(actual).lower()}")
                    for evento in ("click", "keydown.enter", "keydown.space"):
                        tarjeta.on(evento, lambda n=nombreDistribucion: elegir(n))
                    tarjeta.mark(f"opcionDistribucion-{nombreDistribucion}")
                    ui.label(nombreDistribucion or "Ninguna (ver como lista)").classes("font-bold")
                    distribucion = cargarDistribucion(nombreDistribucion) if nombreDistribucion else None
                    if distribucion:
                        ancho, alto = self.medidaDistribucion(distribucion)
                        with ui.element("div").classes("relative").style(f"width: {ancho * unidad}px; height: {alto * unidad}px"):
                            for t in distribucion:
                                estilo = f"left: {t.get('x', 0) * unidad}px; top: {t.get('y', 0) * unidad}px; width: {t.get('w', 1) * unidad - 1}px; height: {t.get('h', 1) * unidad - 1}px"
                                ui.element("div").classes(f"absolute bg-{self.colorTeclaVacia} rounded-sm").style(estilo)
        self.dialogoDistribucion.open()

    def cambiarModoIntercambio(self, dispositivo: dispositivo) -> None:
        """Activa o desactiva el modo intercambiar teclas en la cuadrícula del dispositivo"""
        self.acciónDuplicar.pop(dispositivo.nombre, None)
        if self.teclaIntercambio.pop(dispositivo.nombre, False) is False:
            self.teclaIntercambio[dispositivo.nombre] = None
        self.marcarSelección(dispositivo)

    def cambiarModoDuplicar(self, dispositivo: dispositivo) -> None:
        """Activa o desactiva el modo duplicar acción en la cuadrícula del dispositivo"""
        self.teclaIntercambio.pop(dispositivo.nombre, None)
        if self.acciónDuplicar.pop(dispositivo.nombre, False) is False:
            self.acciónDuplicar[dispositivo.nombre] = None
        self.marcarSelección(dispositivo)

    def clickTecla(self, dispositivo: dispositivo, tecla, acción: dataAccion | None) -> None:
        """Click en una tecla en Editar según el modo actual del dispositivo"""
        nombre = dispositivo.nombre
        if nombre in self.teclaIntercambio:
            self.seleccionarIntercambio(dispositivo, tecla)
        elif nombre in self.acciónDuplicar:
            self.seleccionarDuplicar(dispositivo, tecla, acción)
        elif acción is not None:
            self.siNoHayCambios(lambda: self.seleccionarAcción(acción, dispositivo))
        else:
            self.siNoHayCambios(lambda: self.nuevaAcciónTecla(dispositivo, tecla))

    def marcarTecla(self, dispositivo: dispositivo, tecla, boton: ui.element, acción: dataAccion | None) -> None:
        """Anillo en la tecla elegida para intercambiar o en la acción elegida para duplicar"""
        nombre = dispositivo.nombre
        elegida = (nombre in self.teclaIntercambio and str(tecla) == str(self.teclaIntercambio[nombre])) or (
            acción is not None and acción is self.acciónDuplicar.get(nombre)
        )
        anillo = f"ring-4 ring-{self.colorActivo}"
        boton.classes(add=anillo) if elegida else boton.classes(remove=anillo)

    def pintarHerramientas(self, dispositivo: dispositivo) -> None:
        """Intercambiar y Duplicar se pintan del color activo mientras su modo está encendido"""
        botones = self.herramientasModo.get(dispositivo.nombre, {})
        for modo, activo in (("intercambiar", self.teclaIntercambio), ("duplicar", self.acciónDuplicar)):
            if modo in botones:
                encendido = dispositivo.nombre in activo
                color = self.colorActivo if encendido else self.colorBotones
                botones[modo].classes(remove=f"bg-{self.colorActivo} bg-{self.colorBotones}", add=f"bg-{color}")
                botones[modo].props(f"aria-pressed={str(encendido).lower()}")

    def marcarSelección(self, dispositivo: dispositivo) -> None:
        """Actualiza los anillos de las teclas y los botones de modo sin redibujar la pestaña"""
        for tecla, (boton, acción) in self.teclasDibujadas.get(dispositivo.nombre, {}).items():
            self.marcarTecla(dispositivo, tecla, boton, acción)
        self.pintarHerramientas(dispositivo)

    def seleccionarDuplicar(self, dispositivo: dispositivo, tecla, acción: dataAccion | None) -> None:
        """Primer click elige la acción a copiar, click en una tecla vacía pega la copia; click en otra acción la elige"""
        copiada = self.acciónDuplicar.get(dispositivo.nombre)
        if acción is not None:
            # Click en la misma acción la suelta
            self.acciónDuplicar[dispositivo.nombre] = None if acción is copiada else acción
        elif copiada is not None:
            copia = dataAccion.desdeDict(copy.deepcopy(copiada.aDict()))
            copia.key = tecla
            dispositivo.listaAcciones.append(copia)
            dispositivo.listaAcciones.sort(key=self.ordenTecla)
            dispositivo.salvarAcciones()
            ui.notify(f"{copia.nombre or 'Acción'} duplicada en la tecla {tecla}")
            self.actualizarPestaña(dispositivo)
            return
        self.marcarSelección(dispositivo)

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
                self.actualizarPestaña(dispositivo)
                return
        self.marcarSelección(dispositivo)

    def abrirPropiedadesFolder(self, dispositivo: dispositivo) -> None:
        """Carga en el diálogo la propiedad_folder del folder actual del dispositivo"""
        self.dispositivoFolder = dispositivo
        propiedad = dispositivo.propiedadFolder
        self.editorFolderFondo.value = (propiedad.fondo if propiedad else None) or ""
        self.editorFolderTamaño.value = (propiedad.tituloOpciones.get("tamanno_maximo") if propiedad else None)
        self.filaFolderCuadricula.visible = miGui.usaCuadriculaFolder(dispositivo)
        columnas, filas = dispositivo.cuadriculaFolder() or (None, None)
        self.editorFolderColumnas.value = columnas
        self.editorFolderFilas.value = filas
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
        if self.filaFolderCuadricula.visible:
            columnas, filas = self.editorFolderColumnas.value, self.editorFolderFilas.value
            if columnas and filas:
                propiedad.extra["cuadricula"] = {"columnas": int(columnas), "filas": int(filas)}
            else:
                propiedad.extra.pop("cuadricula", None)

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
        self.recordarFormulario()
        self.mostrarFormularioEnCelular()

    def dibujarBotonera(self, listaAcciones: list[dict], dispositivo: dispositivo) -> None:
        """Modo Usar para dispositivos sin cuadrícula (MQTT, teclado sin distribución): un botón grande por acción"""
        with ui.element("div").classes("grid gap-3 p-4 w-full").style("grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr))"):
            for acción in self.ordenarAcciones(listaAcciones, "key"):
                tecla = acción.get("key")
                if tecla == "propiedad_folder":
                    continue
                boton = ui.button(acción.get("nombre") or str(tecla), color=self.colorTecla)
                self.conectarTecla(boton, acción, dispositivo)
                boton.props("unelevated no-caps").classes("h-20 rounded-xl tecla-viva").tooltip(str(tecla))
                boton.mark(f"tecla-{dispositivo.nombre}-{tecla}")

    def dibujarAcciones(self, listaAcciones: list[dict], dispositivo: dispositivo) -> None:
        """Dibuja las acciones de los dispositivos en la interfaz web

        Args:
            listaAcciones (list[dict]): Lista de acciones a dibujar
        """

        def cabecera(texto: str, campo: str = None, clases: str = "") -> None:
            if campo is None:
                ui.label(texto).classes(f"font-bold {clases}")
                return
            orden = "none"
            if campo == self.ordenCampo:
                texto += " ▼" if self.ordenInverso else " ▲"
                orden = "descending" if self.ordenInverso else "ascending"
            # Botón y no etiqueta: se ordena también con el teclado
            boton = ui.button(texto, on_click=lambda c=campo: self.cambiarOrden(c, dispositivo)).props("flat dense no-caps align=left color=white padding=0")
            boton.classes(f"font-bold justify-self-start {clases}").mark(f"orden-{campo}-{dispositivo.nombre}")
            boton.props["aria-sort"] = orden

        with ui.element("div").classes("fila-acciones cabecera-acciones p-2 border-2 border-transparent"):
            cabecera("Nombre", "nombre")
            cabecera("Título", "titulo", "solo-ancho")
            cabecera("Tecla", "key")
            cabecera("Acción", "accion", "solo-ancho")
            cabecera("Opciones", clases="solo-ancho")

        for acciónActual in self.ordenarAcciones(listaAcciones, self.ordenCampo, self.ordenInverso):
            nombreAcción = acciónActual.get("nombre")
            teclaAcción = acciónActual.get("key")
            if teclaAcción == "propiedad_folder":
                # No es un botón, se edita con "Apariencia del folder"
                continue
            acciónAcción = acciónActual.get("accion")
            tituloAcción = acciónActual.get("titulo")

            with ui.element("div").classes(f"fila-acciones p-2 border-2 border-{self.colorBorde}"):
                ui.label(nombreAcción).tooltip(nombreAcción or "")
                ui.label(tituloAcción).classes("solo-ancho")
                ui.label(teclaAcción)

                claseAcción = self.obtenerAcciónOop(acciónAcción)
                if claseAcción is not None:
                    ui.label(claseAcción().nombre).classes("solo-ancho")
                else:
                    # Acción sin clase OOP (ej. macro): se muestra su comando tal cual
                    ui.label(acciónAcción).classes("solo-ancho")

                marca = f"{dispositivo.nombre}-{teclaAcción}"
                # Una sola celda de la grilla para los tres botones
                with ui.row().classes("no-wrap gap-1 items-center"):
                    with ui.button_group().props("rounded"):
                        miGui.nombrar(ui.button(icon="play_arrow", color=self.colorBotones, on_click=lambda a=acciónActual: self.probarAcción(a)).mark(f"ejecutar-{marca}"), f"Probar {nombreAcción}")
                        miGui.nombrar(ui.button(icon="edit", color=self.colorBotones, on_click=lambda a=acciónActual: self.siNoHayCambios(lambda: self.seleccionarAcción(a, dispositivo))).mark(f"editar-{marca}"), f"Editar {nombreAcción}")
                    miGui.nombrar(ui.button(icon="delete", color=self.colorPeligro, on_click=lambda a=acciónActual, d=dispositivo: self.borrarConDeshacer(a, d)).props("flat round").mark(f"borrar-{marca}"), f"Borrar {nombreAcción}")

    def probarAcción(self, acción: dataAccion) -> None:
        """Botón ▶: presiona y suelta seguido, para que acciones como Presiona no queden a medias"""
        self.buscarAccion(acción, self.estadoTecla.PRESIONADA)
        self.buscarAccion(acción, self.estadoTecla.LIBERADA)

    def buscarAccion(self, acción: dict, estado):
        logger.info(f"Evento[{acción.get('nombre')}] {self.nombre}[{acción.get('key')}-{estado.name}]")
        if estado == self.estadoTecla.LIBERADA:
            self.ejecutarAcción(acción, False)
        else:
            self.ejecutarAcción(acción)

    def borrarAcción(self, accion, dispositivo: dispositivo):
        dispositivo.listaAcciones.remove(accion)
        dispositivo.salvarAcciones()
        self.actualizarPestaña(dispositivo)

    def actualizar(self):

        logger.info("Actualizando GUI")

        super().actualizar()
