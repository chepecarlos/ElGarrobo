import importlib
import logging
import socket
import threading

from nicegui import app, ui

from elGarrobo.dispositivos.dataAccion import dataAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.migui import configuracion, eventos, tema
from elGarrobo.dispositivos.migui.dialogos import crearDialogoConfirmacion, crearDialogoReiniciar
from elGarrobo.dispositivos.migui.editores import encabezado
from elGarrobo.dispositivos.migui.formulario import formularioAccion
from elGarrobo.dispositivos.migui.pestañas import pestañasDispositivos
from elGarrobo.dispositivos.migui.teclas import teclaRepetida
from elGarrobo.dispositivos.migui.vistas import servirVista
from elGarrobo.miLibrerias import ConfigurarLogging, SalvarValor, leerData

# librería https://nicegui.io/
# estilo https://tailwindcss.com/
# iconos https://fonts.google.com/icons


logger = ConfigurarLogging(__name__, logging.INFO)

# importlib: el paquete accionesOOP exporta la clase accionAbrirGUI con el mismo nombre que el submódulo
moduloAbrirGUI = importlib.import_module("elGarrobo.accionesOOP.accionAbrirGUI")

ARCHIVO_PREFERENCIAS = "gui_preferencias"
"Archivo de config con preferencias de la GUI (ej. el último modo Usar/Editar)"

PUERTO_DEFECTO = 8080


def buscarPuertoLibre(inicio: int = PUERTO_DEFECTO, intentos: int = 20) -> int:
    """Primer puerto libre desde inicio, para no chocar con otro sistema cuando gui.md no fija uno"""
    for puerto in range(inicio, inicio + intentos):
        with socket.socket() as prueba:
            # Igual que uvicorn: un puerto en TIME_WAIT de un reinicio reciente cuenta como libre
            prueba.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                prueba.bind(("0.0.0.0", puerto))
                return puerto
            except OSError:
                continue
    return inicio


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

    puerto: int | None = None
    "puerto de la interfaz web; None busca uno libre al conectar"

    folderLabel: ui.label = None
    "Etiqueta con el dispositivo y folder actual"
    ultimaLabel: ui.label = None
    "Etiqueta con la última acción ejecutada en modo Usar"

    def __init__(self, dataConfiguracion: dict) -> None:

        super().__init__(dataConfiguracion)
        self.nombre = dataConfiguracion.get("nombre", "miGui")

        self.puerto = dataConfiguracion.get("puerto")

        self.folder: str = "?"
        self.listaClasesAcciones: dict = dict()
        self.salvarAcciones: callable = None
        self.agregarDispositivo: callable = None
        "elGarrobo.agregarDispositivo: crea y conecta un aparato sin reiniciar"
        self.quitarDispositivo: callable = None
        "elGarrobo.quitarDispositivo: desconecta un aparato por nombre"
        self.ejecutaEvento: callable = None
        self.pestañas: pestañasDispositivos = None
        self.teclasPresionadas: dict[int, tuple[dataAccion, str]] = {}
        "Teclas hundidas en modo Usar: (acción, folder de su dispositivo) para soltarlas igual"
        "id → acción presionada en modo Usar, para mandar soltar una sola vez"
        self.modoUsar: bool = False
        self.nombreTema: str = tema.TEMA_DEFECTO
        "Clave de tema.TEMAS: auto, claro u oscuro"
        "Modo Usar: click en una tecla la ejecuta; modo Editar: la abre en el formulario"
        self.splitter: ui.splitter = None
        self.contenedorFormulario: ui.column = None
        self.formulario: formularioAccion = None
        self.pendientesReinicio: dict[str, str] = {}
        "clave → descripción de los cambios guardados que se aplican al reiniciar; se reemplaza entero para que los bind lo noten"
        self.valoresAlArrancar: dict[str, bool] = {}
        "clave del switch → su valor antes del primer cambio, para quitar el pendiente si se regresa"
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
                        self.formulario = formularioAccion(
                            self.listaClasesAcciones,
                            self.listaDispositivos,
                            pestañaActual=lambda: self.pestañas.tabs.value if self.pestañas else None,
                            alGuardar=self.actualizarPestaña,
                            borrarConDeshacer=self.borrarConDeshacer,
                            probarAcción=self.probarAcción,
                        )
                with self.splitter.after:
                    self.pestañas = pestañasDispositivos(
                        self.listaDispositivos,
                        self.listaClasesAcciones,
                        self.formulario,
                        modoUsar=lambda: self.modoUsar,
                        conectarTecla=self.conectarTecla,
                        probarAcción=self.probarAcción,
                        borrarConDeshacer=self.borrarConDeshacer,
                        alCambiar=self.actualizarCabecera,
                    )
                    # Aparte y no en el constructor: la cabecera que se actualiza al crearlas lee self.pestañas
                    self.pestañas.crearPestañas()
            self.estructura(conModo=True)
            self.aplicarModo()
            # Las etiquetas de la cabecera se crean en estructura(), después de las pestañas
            self.actualizarCabecera()

        @ui.page("/modulos")
        def paginaModulos():
            from elGarrobo.accionesOOP.accionListaCheckBox import accionListaCheckBox
            from elGarrobo.modulos import cargarModulos

            accionListaCheckBox.registrarCliente(ui.context.client)
            aviso = "Activar, apagar o cambiar las opciones de un módulo se aplica al reiniciar ElGarrobo"
            configuracion.mostrarListaActivables("Módulos", "modulos", cargarModulos(), aviso, self)
            self.estructura()

        @ui.page("/dispositivos")
        def paginaDispositivos():
            from elGarrobo.accionesOOP.accionListaCheckBox import accionListaCheckBox
            from elGarrobo.dispositivos import cargarDispositivos

            accionListaCheckBox.registrarCliente(ui.context.client)
            aviso = "Activar o apagar un tipo se aplica al reiniciar ElGarrobo; los aparatos se agregan y quitan al momento"
            # Sin la GUI: apagarla desde aquí dejaba la página sin forma de volver; se enciende con elgarrobo -g
            tipos = [c for c in cargarDispositivos() if c is not miGui]
            configuracion.mostrarListaActivables("Dispositivos", "dispositivos", tipos, aviso, self)
            self.estructura()

        @ui.page("/eventos")
        def paginaEventos():
            eventos.mostrarEventos(self.listaClasesAcciones, self.ejecutarAcción)
            self.estructura()

        @ui.page("/configurar")
        def paginaConfigurar():
            # Antes que el contenido: el selector de tema cambia el dark_mode que crea estructura()
            oscuro = self.estructura()
            configuracion.mostrarConfigurar(self.nombreTema, lambda nombreTema: self.cambiarTema(nombreTema, oscuro))

    def actualizarCabecera(self) -> None:
        """Muestra información del dispositivo rutas de la interfaz web"""
        if self.pestañas is None or self.folderLabel is None:
            return
        dispositivoActual = self.pestañas.dispositivoSeleccionado()
        if dispositivoActual is not None:
            # El dispositivo ya se ve en la pestaña; "/" es el inicio del perfil
            folder = "/" + ("" if dispositivoActual.enFolderRaiz() else str(dispositivoActual.folderActual).strip("/"))
            # title: el folder se recorta con … si no cabe en la cabecera
            self.folderLabel.props["title"] = folder
            self.folderLabel.text = folder
        if self.formulario is not None:
            self.formulario.actualizarTituloFormulario()

    def cambiarModo(self, usar: bool) -> None:
        """Cambia entre Usar y Editar, lo recuerda para la próxima vez y redibuja los dispositivos"""
        self.modoUsar = usar
        SalvarValor(ARCHIVO_PREFERENCIAS, "modo_usar", usar)
        if self.pestañas is not None:
            self.pestañas.limpiarHerramientas()
        self.aplicarModo()
        for dispositivoActual in self.listaDispositivos:
            self.actualizarPestaña(dispositivoActual)

    def cambiarTema(self, nombreTema: str, oscuro: ui.dark_mode) -> None:
        """Aplica el tema en la página y lo recuerda; las otras páginas lo toman al abrirse"""
        self.nombreTema = nombreTema
        oscuro.value = tema.TEMAS[nombreTema]
        SalvarValor(ARCHIVO_PREFERENCIAS, "tema", nombreTema)

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
        presionada = self.teclasPresionadas.pop(id(acción), None)
        if presionada is None:
            return
        self.buscarAccion(acción, self.estadoTecla.LIBERADA, presionada[1])

    def soltarTodas(self) -> None:
        for acción, _ in list(self.teclasPresionadas.values()):
            self.soltarTecla(acción, None)

    def presionarTecla(self, acción: dataAccion, dispositivo: dispositivo) -> None:
        """Ejecuta la acción de una tecla en modo Usar y la muestra en la cabecera"""
        # Mantener Enter/Espacio repite keydown: se ejecuta una sola vez hasta soltar
        if id(acción) in self.teclasPresionadas:
            return
        folder = dispositivo.folderActual
        self.teclasPresionadas[id(acción)] = (acción, folder)
        nombre = acción.get("nombre") or str(acción.get("key"))
        try:
            self.buscarAccion(acción, self.estadoTecla.PRESIONADA, folder)
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
        repetida = teclaRepetida(dispositivo.listaAcciones, acción.get("key"), None)
        if repetida is not None:
            ui.notify(f"No se pudo deshacer: la tecla {acción.get('key')} ya la usa '{repetida.get('nombre')}'", type="warning")
            return
        dispositivo.listaAcciones.insert(posición, acción)
        dispositivo.salvarAcciones()
        self.actualizarPestaña(dispositivo)
        ui.notify(f"{nombre} restaurada en {dispositivo.nombre}", type="positive")

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

    def estructura(self, conModo: bool = False) -> ui.dark_mode:
        """Estructura de la interfaz, cabecera y pie de página

        Args:
            conModo (bool): Página de acciones: muestra dispositivo/folder, última acción y el interruptor Usar/Editar
        Returns:
            ui.dark_mode: Tema claro u oscuro de la página
        """
        oscuro = ui.dark_mode(tema.TEMAS[self.nombreTema])
        ui.add_css(tema.CSS_BOTONERA)
        ui.colors(**tema.COLORES_QUASAR)
        with ui.header(elevated=True) as cabecera:
            cabecera.classes(f"bg-{tema.colorOscuro} items-center justify-between gap-0")
            cabecera.style("padding: 1px")
            encabezado(ui.label("ElGarrobo").classes("text-h5 px-4 sm:px-8"), 1)
            if conModo and self.pestañas is not None:
                cabecera.classes("cabecera-grilla")
                self.pestañas.tabs.move(cabecera)
            # Lado derecho en un solo bloque: en la grilla ocupa la tercera columna; el folder se recorta si no cabe
            with ui.row().classes("items-center justify-end gap-6 no-wrap min-w-0"):
                if conModo:
                    with ui.row().classes("items-center gap-6 no-wrap min-w-0 max-sm:hidden"):
                        with ui.row().classes("items-center gap-1 no-wrap min-w-0"):
                            ui.icon("folder", color=tema.colorClaro)
                            self.folderLabel = ui.label("").classes(f"text-{tema.colorClaro} truncate").mark("cabecera-folder")
                        with ui.row().classes("items-center gap-1 rounded px-2 no-wrap min-w-0") as self.ultimaFila:
                            ui.icon("play_arrow", color=tema.colorClaro)
                            self.ultimaLabel = ui.label("").classes("truncate").mark("ultimaAcción")
                        self.ultimaFila.visible = False
                abrirReiniciar = crearDialogoReiniciar(lambda: self.pendientesReinicio, self.reiniciar)
                dialogoSalir = crearDialogoConfirmacion("¿Cerrar ElGarrobo? Las teclas y esta página dejan de funcionar hasta que lo vuelvas a abrir.", "Salir", self.salir)
                with ui.dialog() as dialogoAcercaDe, ui.card():
                    ui.label("ElGarrobo").classes("text-h6")
                    ui.label("Creado por ChepeCarlos")
                    with ui.row():
                        ui.link("YouTube", "https://www.youtube.com/@chepecarlo", new_tab=True).classes("texto-acento")
                        ui.link("TikTok", "https://www.tiktok.com/@chepecarlo", new_tab=True).classes("texto-acento")
                    ui.button("Cerrar", on_click=dialogoAcercaDe.close).props("flat")
                with ui.row().classes("items-center gap-2 no-wrap"):
                    # En todas las páginas: un cambio hecho en /dispositivos sigue pendiente al volver a Acciones
                    reinicio = ui.button(icon="restart_alt", color=tema.colorPendiente, on_click=abrirReiniciar)
                    reinicio.props("unelevated no-caps text-color=black").mark("reiniciar-pendiente")
                    reinicio.props["aria-label"] = "Reiniciar para aplicar los cambios pendientes"
                    with reinicio:
                        # En celular solo el ícono: la cabecera no tiene espacio
                        ui.label("Reiniciar para aplicar").classes("ml-2 max-sm:hidden")
                        ui.tooltip().bind_text_from(self, "pendientesReinicio", backward=lambda p: "Pendiente: " + ", ".join(p.values()))
                    reinicio.bind_visibility_from(self, "pendientesReinicio", backward=bool)
                    if conModo:
                        modo = ui.toggle({True: "Usar", False: "Editar"}, value=self.modoUsar, on_change=lambda e: self.cambiarModo(e.value))
                        modo.classes("modo-toggle").props("rounded unelevated no-caps toggle-text-color=black text-color=white").props(f"toggle-color={tema.colorSeleccion} color={tema.colorInterruptor}").mark("modo")
                    with ui.button(icon="menu").props("flat color=white aria-label=Menú").classes("px-8"):
                        with ui.menu():
                            ui.menu_item("Acciones", on_click=lambda: ui.navigate.to("/")).mark("menu-Acciones")
                            ui.menu_item("Módulos", on_click=lambda: ui.navigate.to("/modulos")).mark("menu-Módulos")
                            ui.menu_item("Dispositivos", on_click=lambda: ui.navigate.to("/dispositivos")).mark("menu-Dispositivos")
                            ui.menu_item("Eventos", on_click=lambda: ui.navigate.to("/eventos")).mark("menu-Eventos")
                            ui.menu_item("Configurar", on_click=lambda: ui.navigate.to("/configurar")).mark("menu-Configurar")
                            ui.menu_item("Acerca de", on_click=dialogoAcercaDe.open).mark("menu-AcercaDe")
                            ui.separator()
                            ui.menu_item("Reiniciar", on_click=abrirReiniciar).mark("menu-Reiniciar")
                            ui.menu_item("Salir", on_click=dialogoSalir.open).mark("menu-Salir")
        return oscuro


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
        preferencias = leerData(ARCHIVO_PREFERENCIAS) or {}
        self.modoUsar = bool(preferencias.get("modo_usar", False))
        nombreTema = preferencias.get("tema")
        self.nombreTema = nombreTema if nombreTema in tema.TEMAS else tema.TEMA_DEFECTO

        # Puerto asignado por el usuario se usa tal cual, aunque falle; si no hay, el primero libre
        if self.puerto is None:
            self.puerto = buscarPuertoLibre()
        moduloAbrirGUI.puertoEnUso = self.puerto
        logger.info(f"GUI en http://localhost:{self.puerto}")

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
                # Tema de la primera carga, antes de que ui.dark_mode de estructura() lo aplique: sin destello del otro tema
                dark=tema.TEMAS[self.nombreTema],
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
        if self.pestañas is not None:
            self.pestañas.mostrarPestañas()

    def actualizarPestaña(self, dispositivo: dispositivo) -> None:
        """Redibuja la pestaña del dispositivo, si ya se abrió la página de acciones"""
        if self.pestañas is not None:
            self.pestañas.actualizarPestaña(dispositivo)

    def probarAcción(self, acción: dataAccion, dispositivoAcción: dispositivo | None = None) -> None:
        """Botón ▶: presiona y suelta seguido, para que acciones como Presiona no queden a medias

        Con dispositivoAcción las rutas ./x se buscan en su folder actual, como al presionar su tecla
        """
        folder = (dispositivoAcción or self).folderActual
        self.buscarAccion(acción, self.estadoTecla.PRESIONADA, folder)
        self.buscarAccion(acción, self.estadoTecla.LIBERADA, folder)

    def buscarAccion(self, acción: dict, estado, folder: str | None = None):
        logger.info(f"Evento[{acción.get('nombre')}] {self.nombre}[{acción.get('key')}-{estado.name}]")
        folder = self.folderActual if folder is None else folder
        self.ejecutarAcción(acción, estado != self.estadoTecla.LIBERADA, 1, folder)

    def borrarAcción(self, accion, dispositivo: dispositivo):
        dispositivo.listaAcciones.remove(accion)
        dispositivo.salvarAcciones()
        self.actualizarPestaña(dispositivo)

    def actualizar(self):

        logger.info("Actualizando GUI")

        super().actualizar()
