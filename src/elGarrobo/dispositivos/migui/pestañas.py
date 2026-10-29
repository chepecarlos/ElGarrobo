"""Pestañas de los dispositivos: dibuja cada uno como su aparato (cuadrícula, teclado, StreamDeck Plus) o como lista,
con la barra de herramientas para navegar folders y páginas, intercambiar y duplicar teclas
"""

import copy
import logging
from pathlib import Path

from nicegui import ui

from elGarrobo.dispositivos.dataAccion import dataAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.mideck.mi_streamdeck_plus import MiStreamDeckPlus
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.configuracion import dialogoOrdenPestañas
from elGarrobo.dispositivos.migui.distribucion import dialogoDistribucion, medidaDistribucion
from elGarrobo.dispositivos.migui.editores import nombrar
from elGarrobo.dispositivos.migui.folder import dialogoFolder, usaCuadriculaFolder
from elGarrobo.dispositivos.migui.formulario import formularioAccion
from elGarrobo.dispositivos.migui.teclas import ordenarAcciones, ordenTecla, tamañoTecla, unidadTecla
from elGarrobo.dispositivos.migui.vistas import urlVista
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__, logging.INFO)


class pestañasDispositivos:
    """Una pestaña por dispositivo; en Editar un click en una tecla la abre en el formulario, en Usar la ejecuta"""

    def __init__(
        self,
        listaDispositivos: list[dispositivo],
        listaClasesAcciones: dict,
        formulario: formularioAccion,
        modoUsar,
        conectarTecla,
        probarAcción,
        borrarConDeshacer,
        alCambiar,
    ) -> None:
        """Crea las pestañas y sus paneles donde se llama; las pestañas se mueven a la cabecera en miGui.estructura()

        Args:
            listaDispositivos (list): dispositivos conectados, se ordenan por nivelOrdenar al crear las pestañas
            listaClasesAcciones (dict): comando → clase de la acción, para mostrar su nombre en la lista
            formulario (formularioAccion): formulario donde se abre la tecla al hacer click en Editar
            modoUsar: devuelve True en modo Usar (las teclas se ejecutan) y False en Editar
            conectarTecla: en Usar conecta un botón para presionar y soltar su acción como el aparato
            probarAcción: ejecuta una acción como si se presionara su tecla (botón ▶ de la lista)
            borrarConDeshacer: borra una acción de un dispositivo con aviso para deshacer
            alCambiar: se llama al cambiar de pestaña o redibujar un dispositivo, para actualizar la cabecera
        """
        self.listaDispositivos = listaDispositivos
        self.listaClasesAcciones = listaClasesAcciones
        self.formulario = formulario
        self.modoUsar = modoUsar
        self.conectarTecla = conectarTecla
        self.probarAcción = probarAcción
        self.borrarConDeshacer = borrarConDeshacer
        self.alCambiar = alCambiar
        self.panel: dict[str, ui.tab_panel] = {}
        "dispositivo → panel de su pestaña"
        self.pestaña: dict[str, ui.tab] = {}
        "dispositivo → su pestaña, para moverla al cambiar el orden"
        self.ordenCampo: str = "key"
        self.ordenInverso: bool = False
        self.dispositivosEnLista: set[str] = set()
        "Dispositivos con distribución física que el usuario cambió a vista de lista"
        self.teclaIntercambio: dict = {}
        "Dispositivos en modo intercambiar → primera tecla seleccionada (None si aún no hay)"
        self.acciónDuplicar: dict[str, dataAccion | None] = {}
        "dispositivo → acción a copiar en modo duplicar; guarda la acción y no la tecla para poder pegarla en otra página o folder"
        self.teclasDibujadas: dict[str, dict[str, tuple[ui.element, dataAccion | None]]] = {}
        "dispositivo → tecla → (botón, acción) de la cuadrícula en Editar, para marcar la selección sin redibujar"
        self.herramientasModo: dict[str, dict[str, ui.button]] = {}
        "dispositivo → botones Intercambiar y Duplicar de la barra, para pintarlos sin redibujar"
        self.últimaVista: dict[str, tuple[Path, int]] = {}
        "dispositivo → (folder, página) dibujados la última vez, para saber hacia dónde se navegó"

        self.propiedadesFolder = dialogoFolder(self.actualizarPestaña)
        self.distribuciones = dialogoDistribucion(self.actualizarPestaña)
        self.abrirOrden = dialogoOrdenPestañas(listaDispositivos, self.reordenarPestañas)
        self.tabs = ui.tabs(on_change=alCambiar).props("outside-arrows mobile-arrows")
        # Se mueven a la cabecera en miGui.estructura()
        self.tabs.classes("cabecera-pestañas text-white")
        self.paneles = ui.tab_panels(self.tabs)
        self.paneles.classes("w-full")

    def limpiarHerramientas(self) -> None:
        """Intercambiar y duplicar son herramientas de edición, no deben seguir activas en Usar"""
        self.teclaIntercambio.clear()
        self.acciónDuplicar.clear()

    def cambiarOrden(self, campo: str, dispositivo: dispositivo) -> None:
        """Ordena por campo; si ya estaba ordenado por ese campo invierte el sentido"""
        self.ordenInverso = not self.ordenInverso if self.ordenCampo == campo else False
        self.ordenCampo = campo
        self.actualizarPestaña(dispositivo)

    def crearPestañas(self) -> None:
        """Crea las pestañas de los dispositivos"""
        if self.tabs is None or self.paneles is None:
            logger.warning("No hay pestañas o paneles para mostrar")
            return

        self.listaDispositivos.sort(key=lambda x: x.nivelOrdenar, reverse=True)

        with self.tabs:
            for dispositivoActual in self.listaDispositivos:
                nombreDispositivo: str = dispositivoActual.nombre
                # Cambiar de pestaña no limpia el formulario: la edición sigue ligada a su dispositivo (ver tituloFormulario)
                pestaña = self.pestaña[nombreDispositivo] = ui.tab(nombreDispositivo)

                with self.paneles:
                    self.panel[nombreDispositivo] = ui.tab_panel(pestaña)
                    with self.panel[nombreDispositivo]:
                        ui.label(f"Cargando acciones de {nombreDispositivo}...")
                dispositivoActual.funcionActualizarPestaña = self.actualizarPestaña

        self.mostrarPestañas()

    def reordenarPestañas(self) -> None:
        """Mueve las pestañas al orden de nivelOrdenar sin redibujar los paneles"""
        self.listaDispositivos.sort(key=lambda x: x.nivelOrdenar, reverse=True)
        # Los agregados desde /dispositivos después de abrir la página todavía no tienen pestaña
        conPestaña = [self.pestaña[d.nombre] for d in self.listaDispositivos if d.nombre in self.pestaña]
        for posición, pestaña in enumerate(conPestaña):
            pestaña.move(target_index=posición)

    def mostrarPestañas(self) -> None:

        if self.tabs is None or self.paneles is None:
            logger.warning("No hay pestañas o paneles para mostrar")
            return

        for dispositivoActual in self.listaDispositivos:
            self.actualizarPestaña(dispositivoActual)

        for dispositivoActual in self.listaDispositivos:
            nombreDispositivo = dispositivoActual.nombre
            self.paneles.value = nombreDispositivo
            self.paneles.update()
            self.alCambiar()
            return

    def dispositivoSeleccionado(self, nombreDispositivo: str = None) -> dispositivo:
        """Busca la instancia real del dispositivo por nombre de pestaña

        Args:
            nombreDispositivo (str, optional): Nombre de la pestaña, por defecto la seleccionada
        """
        nombreDispositivo = nombreDispositivo or self.tabs.value
        for dispositivoActual in self.listaDispositivos:
            if dispositivoActual.nombre == nombreDispositivo:
                return dispositivoActual
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

        panel = self.panel.get(nombre)
        if panel is None:
            logger.warning(f"dispositivo {nombre} sin panel")
            return

        with self.paneles:
            panel.clear()
            # Las teclas y herramientas viejas ya no existen; dibujarCuadricula y barraHerramientas las vuelven a guardar
            self.teclasDibujadas.pop(nombre, None)
            self.herramientasModo.pop(nombre, None)
            with panel:
                acciones = dispositivo.listaAcciones
                cuadricula = dispositivo.gruposBotones() is not None or dispositivo.distribucionTeclas() is not None
                usar = self.modoUsar()
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

            self.alCambiar()

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
        usar = self.modoUsar()
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
        usar = self.modoUsar()
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
            if len(self.listaDispositivos) > 1:
                orden = ui.button(icon="tab", color=tema.colorBotones, on_click=self.abrirOrden).mark(f"ordenarPestañas-{nombre}")
                nombrar(orden, "Ordenar pestañas")

    def dibujarControlesPlus(self, plus, accionesPorTecla: dict, alClick, marcar) -> None:
        """Pantalla táctil y perillas del StreamDeck Plus, debajo de sus teclas y del mismo ancho

        La pantalla se divide en tantas zonas como acciones touchscreen_N haya, igual que el aparato;
        en Editar se agrega una zona vacía al final para crear la siguiente.
        """
        usar = self.modoUsar()
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
            # color=None: sin el primary de NiceGUI, el texto es el de la página como en "Opciones"
            boton = ui.button(texto, color=None, on_click=lambda c=campo: self.cambiarOrden(c, dispositivo)).props("flat dense no-caps align=left padding=0")
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

                claseAcción = self.listaClasesAcciones.get(acciónAcción)
                if claseAcción is not None:
                    ui.label(claseAcción().nombre).classes("solo-ancho")
                else:
                    # Acción sin clase OOP (ej. macro): se muestra su comando tal cual
                    ui.label(acciónAcción).classes("solo-ancho")

                marca = f"{dispositivo.nombre}-{teclaAcción}"
                # Una sola celda de la grilla para los tres botones
                with ui.row().classes("no-wrap gap-1 items-center"):
                    with ui.button_group().props("rounded"):
                        nombrar(ui.button(icon="play_arrow", color=tema.colorBotones, on_click=lambda a=acciónActual, d=dispositivo: self.probarAcción(a, d)).mark(f"ejecutar-{marca}"), f"Probar {nombreAcción}")
                        nombrar(ui.button(icon="edit", color=tema.colorBotones, on_click=lambda a=acciónActual: self.formulario.siNoHayCambios(lambda: self.formulario.seleccionarAcción(a, dispositivo))).mark(f"editar-{marca}"), f"Editar {nombreAcción}")
                    nombrar(ui.button(icon="delete", color=tema.colorPeligro, on_click=lambda a=acciónActual, d=dispositivo: self.borrarConDeshacer(a, d)).props("flat round").mark(f"borrar-{marca}"), f"Borrar {nombreAcción}")
