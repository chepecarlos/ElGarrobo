import copy
import logging
import threading
from pathlib import Path

from nicegui import app, ui

from elGarrobo.accionesOOP import accion
from elGarrobo.dispositivos.dataAccion import dataAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.mideck.mi_streamdeck_plus import MiStreamDeckPlus
from elGarrobo.dispositivos.migui import configuracion, tema
from elGarrobo.dispositivos.migui.dialogos import crearDialogoConfirmacion
from elGarrobo.dispositivos.migui.distribucion import dialogoDistribucion, medidaDistribucion
from elGarrobo.dispositivos.migui.editores import encabezado, nombrar
from elGarrobo.dispositivos.migui.folder import dialogoFolder, usaCuadriculaFolder
from elGarrobo.dispositivos.migui.formulario import formularioAccion
from elGarrobo.dispositivos.migui.teclas import ordenarAcciones, ordenTecla, tamañoTecla, teclaRepetida, unidadTecla
from elGarrobo.dispositivos.migui.vistas import servirVista, urlVista
from elGarrobo.miLibrerias import ConfigurarLogging, SalvarValor, leerData

# librería https://nicegui.io/
# estilo https://tailwindcss.com/
# iconos https://fonts.google.com/icons


logger = ConfigurarLogging(__name__, logging.INFO)

ARCHIVO_PREFERENCIAS = "gui_preferencias"
"Archivo de config con preferencias de la GUI (ej. el último modo Usar/Editar)"


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
        self.pestañas = None
        self.paneles: ui.tab_panel = None
        self.ordenCampo: str = "key"
        self.dispositivosEnLista: set[str] = set()
        "Dispositivos con distribución física que el usuario cambió a vista de lista"
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
        self.contenedorFormulario: ui.column = None
        self.formulario: formularioAccion = None
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
                            pestañaActual=lambda: self.pestañas.value if self.pestañas else None,
                            alGuardar=self.actualizarPestaña,
                            borrarConDeshacer=self.borrarConDeshacer,
                            probarAcción=self.probarAcción,
                        )
                    self.propiedadesFolder = dialogoFolder(self.actualizarPestaña)
                    self.distribuciones = dialogoDistribucion(self.actualizarPestaña)
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
            configuracion.mostrarListaActivables("Módulos", "modulos", cargarModulos())
            self.estructura()

        @ui.page("/dispositivos")
        def paginaDispositivos():
            from elGarrobo.accionesOOP.accionListaCheckBox import accionListaCheckBox
            from elGarrobo.dispositivos import cargarDispositivos

            accionListaCheckBox.registrarCliente(ui.context.client)
            configuracion.mostrarListaActivables("Dispositivos", "dispositivos", cargarDispositivos())
            self.estructura()

        @ui.page("/configurar")
        def paginaConfigurar():
            configuracion.mostrarConfigurar()
            self.estructura()

    def cambiarOrden(self, campo: str, dispositivo: dispositivo) -> None:
        """Ordena por campo; si ya estaba ordenado por ese campo invierte el sentido"""
        self.ordenInverso = not self.ordenInverso if self.ordenCampo == campo else False
        self.ordenCampo = campo
        self.actualizarPestaña(dispositivo)

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
        if self.formulario is not None:
            self.formulario.actualizarTituloFormulario()

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
        ui.add_css(tema.CSS_BOTONERA)
        ui.colors(**tema.COLORES_QUASAR)
        with ui.header(elevated=True) as cabecera:
            cabecera.classes(f"bg-{tema.colorOscuro} items-center justify-between gap-0")
            cabecera.style("padding: 1px")
            encabezado(ui.label("ElGarrobo").classes("text-h5 px-4 sm:px-8"), 1)
            if conModo and self.pestañas is not None:
                cabecera.classes("cabecera-grilla")
                self.pestañas.move(cabecera)
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
                dialogoReiniciar = crearDialogoConfirmacion("¿Reiniciar ElGarrobo? Las teclas no responden mientras arranca.", "Reiniciar", self.reiniciar)
                dialogoSalir = crearDialogoConfirmacion("¿Cerrar ElGarrobo? Las teclas y esta página dejan de funcionar hasta que lo vuelvas a abrir.", "Salir", self.salir)
                with ui.dialog() as dialogoAcercaDe, ui.card():
                    ui.label("ElGarrobo").classes("text-h6")
                    ui.label("Creado por ChepeCarlos")
                    with ui.row():
                        ui.link("YouTube", "https://www.youtube.com/@chepecarlo", new_tab=True).classes(f"text-{tema.colorClaro}")
                        ui.link("TikTok", "https://www.tiktok.com/@chepecarlo", new_tab=True).classes(f"text-{tema.colorClaro}")
                    ui.button("Cerrar", on_click=dialogoAcercaDe.close).props("flat")
                with ui.row().classes("items-center gap-2 no-wrap"):
                    if conModo:
                        modo = ui.toggle({True: "Usar", False: "Editar"}, value=self.modoUsar, on_change=lambda e: self.cambiarModo(e.value))
                        modo.classes("modo-toggle").props("rounded unelevated no-caps toggle-text-color=black text-color=white").props(f"toggle-color={tema.colorSeleccion} color={tema.colorInterruptor}").mark("modo")
                    with ui.button(icon="menu").props("flat color=white aria-label=Menú").classes("px-8"):
                        with ui.menu():
                            ui.menu_item("Acciones", on_click=lambda: ui.navigate.to("/")).mark("menu-Acciones")
                            ui.menu_item("Módulos", on_click=lambda: ui.navigate.to("/modulos")).mark("menu-Módulos")
                            ui.menu_item("Dispositivos", on_click=lambda: ui.navigate.to("/dispositivos")).mark("menu-Dispositivos")
                            ui.menu_item("Configurar", on_click=lambda: ui.navigate.to("/configurar")).mark("menu-Configurar")
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
                    areaScroll.classes("w-full" if usar else f"w-full border-2 border-{tema.colorBorde}")
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
            unidad = unidadTecla
            dibujo = dispositivo.dibujo()
            ancho, alto = medidaDistribucion(distribucion)
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
                        tamaño = tamañoTecla(teclaFisica)
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
                            boton = ui.button(acción.get("nombre") if acción else etiqueta, color=tema.colorTecla if acción else tema.colorTeclaVacia, on_click=alClick(tecla, acción))
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
                                    boton = ui.element("div").classes(f"rounded bg-{tema.colorTeclaApagada}").style(medidaTecla)
                                else:
                                    boton = ui.button(icon="add", color=tema.colorTeclaVacia, on_click=alClick(tecla, acción)).style(medidaTecla)
                                    boton.props["aria-label"] = f"Agregar acción en la tecla {tecla}"
                                marcar(boton, tecla)
                                if not usar:
                                    etiqueta = f"{tecla}: {acción.get('nombre')}" if acción is not None else str(tecla)
                                    ui.label(etiqueta).classes("text-xs truncate text-center").style(medidaTecla.split(";")[0]).tooltip(etiqueta)
                    if isinstance(dibujante, MiStreamDeckPlus):
                        self.dibujarControlesPlus(dibujante, accionesPorTecla, alClick, marcar)
        if usaCuadriculaFolder(dispositivo):
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
                boton = ui.button(acción.get("nombre"), color=tema.colorTecla, on_click=alClick(tecla, acción)).props("dense no-caps")
                boton.classes("text-xs tecla-viva").tooltip(tecla)
                marcar(boton, tecla)

    def barraHerramientas(self, dispositivo: dispositivo, cuadricula: bool) -> None:
        """Fila sobre el área del dispositivo: subir folder, páginas, herramientas de edición y la vista Cuadrícula/Lista"""
        nombre = dispositivo.nombre
        usar = self.modoUsar
        enLista = cuadricula and nombre in self.dispositivosEnLista
        with ui.row().classes("items-center p-2 w-full gap-2"):
            subir = ui.button(icon="arrow_upward", color=tema.colorBotones, on_click=lambda: self.subirFolder(dispositivo)).mark(f"subirFolder-{nombre}")
            nombrar(subir, "Subir al folder anterior")
            subir.set_enabled(not dispositivo.enFolderRaiz())
            if hasattr(dispositivo, "siguientePagina") and cuadricula and not enLista:
                anterior = ui.button(icon="chevron_left", color=tema.colorBotones, on_click=lambda: self.cambiarPagina(dispositivo, dispositivo.anteriorPagina)).mark(f"paginaAnterior-{nombre}")
                nombrar(anterior, "Página anterior").set_enabled(dispositivo.puedeAnteriorPagina())
                ui.label(f"Página {dispositivo.paginaActual()}").mark(f"pagina-{nombre}")
                siguiente = ui.button(icon="chevron_right", color=tema.colorBotones, on_click=lambda: self.cambiarPagina(dispositivo, lambda: dispositivo.siguientePagina(not usar))).mark(f"paginaSiguiente-{nombre}")
                nombrar(siguiente, "Página siguiente").set_enabled(dispositivo.puedeSiguientePagina(not usar))
            if usar:
                return
            ui.space()
            if cuadricula and not enLista:
                intercambiar = ui.button(icon="swap_horiz", color=tema.colorBotones, on_click=lambda: self.cambiarModoIntercambio(dispositivo)).mark(f"intercambiar-{nombre}")
                nombrar(intercambiar, "Intercambiar teclas")
                duplicar = ui.button(icon="content_copy", color=tema.colorBotones, on_click=lambda: self.cambiarModoDuplicar(dispositivo)).mark(f"duplicar-{nombre}")
                nombrar(duplicar, "Duplicar acción")
                self.herramientasModo[nombre] = {"intercambiar": intercambiar, "duplicar": duplicar}
                self.pintarHerramientas(dispositivo)
            apariencia = ui.button(icon="folder_special", color=tema.colorBotones, on_click=lambda: self.propiedadesFolder.abrir(dispositivo)).mark(f"propiedadesFolder-{nombre}")
            nombrar(apariencia, "Apariencia del folder")
            if hasattr(dispositivo, "cambiarDistribucion"):
                self.botonDistribucion(dispositivo)
            if cuadricula:
                with ui.button_group().props("unelevated rounded"):
                    for lista, icono, texto in ((False, "grid_view", "Vista cuadrícula"), (True, "view_list", "Vista lista")):
                        activo = lista == enLista
                        vista = ui.button(icon=icono, on_click=lambda lista=lista: self.cambiarVista(dispositivo, lista))
                        vista.props(f"color={tema.colorSeleccion if activo else tema.colorInterruptor} text-color={'black' if activo else 'white'}")
                        vista.props["aria-pressed"] = activo
                        nombrar(vista, texto).mark(f"vista-{'lista' if lista else 'cuadricula'}-{nombre}")

    def dibujarControlesPlus(self, plus, accionesPorTecla: dict, alClick, marcar) -> None:
        """Pantalla táctil y perillas del StreamDeck Plus, debajo de sus teclas y del mismo ancho

        La pantalla se divide en tantas zonas como acciones touchscreen_N haya, igual que el aparato;
        en Editar se agrega una zona vacía al final para crear la siguiente.
        """
        usar = self.modoUsar
        nombre = plus.nombre

        def control(tecla: str, descripción: str, icono: str | None = None, texto: str | None = None) -> ui.button:
            acción = accionesPorTecla.get(tecla)
            boton = ui.button(texto, icon=icono, color=tema.colorTecla if acción else tema.colorTeclaVacia, on_click=alClick(tecla, acción))
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
                    ui.element("div").classes(f"w-full rounded bg-{tema.colorTeclaApagada}").style(f"aspect-ratio: {plus.anchoBarra} / {plus.altoBarra}")
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

    def botonDistribucion(self, dispositivo: dispositivo) -> None:
        distribucion = ui.button(icon="keyboard", color=tema.colorBotones, on_click=lambda: self.distribuciones.abrir(dispositivo)).mark(f"distribucion-{dispositivo.nombre}")
        nombrar(distribucion, "Distribución del teclado")

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
            self.formulario.siNoHayCambios(lambda: self.formulario.seleccionarAcción(acción, dispositivo))
        else:
            self.formulario.siNoHayCambios(lambda: self.formulario.nuevaAcciónTecla(dispositivo, tecla))

    def marcarTecla(self, dispositivo: dispositivo, tecla, boton: ui.element, acción: dataAccion | None) -> None:
        """Anillo en la tecla elegida para intercambiar o en la acción elegida para duplicar"""
        nombre = dispositivo.nombre
        elegida = (nombre in self.teclaIntercambio and str(tecla) == str(self.teclaIntercambio[nombre])) or (
            acción is not None and acción is self.acciónDuplicar.get(nombre)
        )
        anillo = f"ring-4 ring-{tema.colorActivo}"
        boton.classes(add=anillo) if elegida else boton.classes(remove=anillo)

    def pintarHerramientas(self, dispositivo: dispositivo) -> None:
        """Intercambiar y Duplicar se pintan del color activo mientras su modo está encendido"""
        botones = self.herramientasModo.get(dispositivo.nombre, {})
        for modo, activo in (("intercambiar", self.teclaIntercambio), ("duplicar", self.acciónDuplicar)):
            if modo in botones:
                encendido = dispositivo.nombre in activo
                color = tema.colorActivo if encendido else tema.colorBotones
                botones[modo].classes(remove=f"bg-{tema.colorActivo} bg-{tema.colorBotones}", add=f"bg-{color}")
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
            dispositivo.listaAcciones.sort(key=ordenTecla)
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
                dispositivo.listaAcciones.sort(key=ordenTecla)
                dispositivo.salvarAcciones()
                self.actualizarPestaña(dispositivo)
                return
        self.marcarSelección(dispositivo)

    def subirFolder(self, dispositivo: dispositivo) -> None:
        """Carga el folder anterior en el dispositivo; avisa a la GUI al cargar"""
        dispositivo.regresarFolderActual()
        dispositivo.actualizar()

    def cambiarPagina(self, dispositivo: dispositivo, cambiar) -> None:
        """Cambia la página del dispositivo físico; el dispositivo avisa a la GUI para redibujar la pestaña"""
        cambiar()
        dispositivo.actualizar()

    def dibujarBotonera(self, listaAcciones: list[dict], dispositivo: dispositivo) -> None:
        """Modo Usar para dispositivos sin cuadrícula (MQTT, teclado sin distribución): un botón grande por acción"""
        with ui.element("div").classes("grid gap-3 p-4 w-full").style("grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr))"):
            for acción in ordenarAcciones(listaAcciones, "key"):
                tecla = acción.get("key")
                if tecla == "propiedad_folder":
                    continue
                boton = ui.button(acción.get("nombre") or str(tecla), color=tema.colorTecla)
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

        for acciónActual in ordenarAcciones(listaAcciones, self.ordenCampo, self.ordenInverso):
            nombreAcción = acciónActual.get("nombre")
            teclaAcción = acciónActual.get("key")
            if teclaAcción == "propiedad_folder":
                # No es un botón, se edita con "Apariencia del folder"
                continue
            acciónAcción = acciónActual.get("accion")
            tituloAcción = acciónActual.get("titulo")

            with ui.element("div").classes(f"fila-acciones p-2 border-2 border-{tema.colorBorde}"):
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
                        nombrar(ui.button(icon="play_arrow", color=tema.colorBotones, on_click=lambda a=acciónActual: self.probarAcción(a)).mark(f"ejecutar-{marca}"), f"Probar {nombreAcción}")
                        nombrar(ui.button(icon="edit", color=tema.colorBotones, on_click=lambda a=acciónActual: self.formulario.siNoHayCambios(lambda: self.formulario.seleccionarAcción(a, dispositivo))).mark(f"editar-{marca}"), f"Editar {nombreAcción}")
                    nombrar(ui.button(icon="delete", color=tema.colorPeligro, on_click=lambda a=acciónActual, d=dispositivo: self.borrarConDeshacer(a, d)).props("flat round").mark(f"borrar-{marca}"), f"Borrar {nombreAcción}")

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
