"""Diálogo para agregar un aparato (teclado, pedal, StreamDeck o grupo de StreamDeck): buscarlo y luego configurarlo"""

import asyncio
import re

from evdev import InputDevice, ecodes
from nicegui import background_tasks, ui

from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.distribucion import ayudaDistribuciones, miniatura
from elGarrobo.dispositivos.migui.editores import campoPropiedad, encabezado, marcarError
from elGarrobo.dispositivos.miteclado.mi_teclado_macro import (
    cargarDistribucion,
    distribucionesDisponibles,
)


async def escucharTeclado(ruta: str, alPresionar) -> None:
    """Llama alPresionar(ruta, tecla) con cada tecla presionada

    Sin grab: si es el teclado principal, se sigue escribiendo
    """
    try:
        teclado = InputDevice(ruta)
    except OSError:
        return
    try:
        async for evento in teclado.async_read_loop():
            if evento.type == ecodes.EV_KEY and evento.value == 1:
                tecla = ecodes.KEY.get(evento.code, evento.code)
                # Algunos códigos tienen varios nombres (ej. KEY_MUTE / KEY_MIN_INTERESTING)
                alPresionar(ruta, tecla[0] if isinstance(tecla, list) else tecla)
    except OSError:
        pass  # se desconectó mientras se escuchaba
    finally:
        teclado.close()


def marcarTarjeta(tarjetas: dict, elegida) -> None:
    """Borde de color en la tarjeta elegida, sin borde en las demás"""
    borde = f"border-2 border-{tema.colorActivo}"
    for clave, tarjeta in tarjetas.items():
        tarjeta.classes(add=borde) if clave == elegida else tarjeta.classes(remove=borde)
        tarjeta.props(f"aria-pressed={str(clave == elegida).lower()}")


def tarjetaElegible(tarjeta: ui.card, alElegir) -> None:
    """Se elige con click, Enter o espacio"""
    tarjeta.classes("cursor-pointer").props("tabindex=0 role=button")
    for evento in ("click", "keydown.enter", "keydown.space"):
        tarjeta.on(evento, alElegir)


class dialogoAgregar:
    """Paso 1 (con listarDisponibles): lista los aparatos; en teclados el que recibe una tecla queda elegido.
    Paso 2: nombre y en Avanzado el archivo de acciones (con prefijoArchivo); los teclados además eligen
    distribución y las teclas que se presionan se iluminan en las miniaturas"""

    def __init__(
        self,
        titulo: str,
        alGuardar,
        listarDisponibles=None,
        prefijoArchivo: str | None = None,
        conTeclas: bool = False,
        propiedades: list | None = None,
    ) -> None:
        """
        Args:
            titulo (str): ej. "Agregar teclado"
            alGuardar: recibe la data del aparato nuevo (entrada de teclados.md, pedal.md…)
            listarDisponibles: devuelve [(ruta o serial, nombre)]; sin ella no hay paso Buscar (ej. un grupo vacío)
            prefijoArchivo (str): del archivo de acciones por defecto (<prefijo>_<nombre>); sin él no se pide archivo
            conTeclas (bool): teclados, se escuchan con evdev y tienen distribución
            propiedades (list): propiedadAccion que se piden en Configurar (ej. broker y puerto de MQTT)
        """
        self.titulo = titulo
        self.alGuardar = alGuardar
        self.listarDisponibles = listarDisponibles
        self.prefijoArchivo = prefijoArchivo
        self.conTeclas = conTeclas
        self.propiedades = propiedades or []
        self.datos: dict = {}
        "Lo escrito en los campos de propiedades"
        self.editores: list = []
        self.disponibles: dict[str, str] = {}
        "ruta → nombre de lo listado en el paso 1 (ej. el modelo de un StreamDeck)"
        self.escuchas: list[asyncio.Task] = []
        self.ruta: str | None = None
        "Teclado elegido en el paso 1"
        self.distribucion: str | None = None
        "Distribución elegida en el paso 2"
        self.nombresUsados: set[str] = set()
        with ui.dialog() as self.dialogo, ui.card().classes("w-full max-w-2xl"):
            self.contenido = ui.column().classes("w-full")
        self.dialogo.on_value_change(lambda e: None if e.value else self.dejarDeEscuchar())
        # Si se cierra el navegador con el diálogo abierto
        ui.context.client.on_delete(self.dejarDeEscuchar)

    def abrir(self, rutasUsadas: set[str], nombresUsados: set[str]) -> None:
        """
        Args:
            rutasUsadas (set): rutas o seriales que ya están en el archivo, se muestran pero no se pueden elegir
            nombresUsados (set): nombres en minúsculas de todos los dispositivos; las pestañas se buscan por nombre
        """
        self.ruta = None
        self.distribucion = None
        self.nombresUsados = nombresUsados
        self.tarjetasTeclado: dict[str, ui.card] = {}
        self.teclaTeclado: dict[str, ui.label] = {}
        self.contenido.clear()
        with self.contenido:
            encabezado(ui.label(self.titulo).classes("text-lg"), 2)
            with ui.stepper().props("flat animated").classes("w-full") as self.pasos:
                if self.listarDisponibles:
                    with ui.step("Buscar"):
                        self.pasoBuscar(rutasUsadas)
                with ui.step("Configurar"):
                    self.pasoConfigurar()
        self.escuchar(list(self.tarjetasTeclado), self.elegir)
        self.dialogo.open()

    def pasoBuscar(self, rutasUsadas: set[str]) -> None:
        disponibles = self.listarDisponibles()
        self.disponibles = dict(disponibles)
        if self.conTeclas:
            ui.label("Presiona una tecla en el teclado que quieres agregar").classes("texto-acento")
        else:
            ui.label("Elige el que quieres agregar").classes("texto-acento")
        if not disponibles:
            # ponytail: los que ya usa ElGarrobo u otro programa no se pueden abrir y no salen
            ui.label("No se encontró ninguno libre conectado").classes("text-caption")
        for ruta, nombre in disponibles:
            usado = ruta in rutasUsadas
            with ui.card().classes("w-full p-2" + (" opacity-50" if usado else "")) as tarjeta:
                tarjeta.mark(f"teclado-{ruta}")
                with ui.row().classes("w-full items-center no-wrap"):
                    with ui.column().classes("gap-0 grow"):
                        ui.label(nombre).classes("font-bold")
                        ui.label("Ya agregado" if usado else ruta.rsplit("/", 1)[-1]).classes("text-caption")
                    tecla = ui.label("").classes("font-mono")
            if not usado:
                # Click por si el teclado no tiene teclas normales (ej. un pedal que manda KEY_F13)
                tarjetaElegible(tarjeta, lambda r=ruta: self.elegir(r))
                self.tarjetasTeclado[ruta] = tarjeta
                self.teclaTeclado[ruta] = tecla
        with ui.stepper_navigation():
            ui.button("Cancelar", on_click=self.dialogo.close).props("flat")
            self.botonSiguiente = ui.button("Siguiente", color=tema.colorOscuro, on_click=self.irAConfigurar)
            self.botonSiguiente.mark("agregar-siguiente").disable()

    def pasoConfigurar(self) -> None:
        self.nombre = ui.input("Nombre", on_change=self.mostrarArchivoPorDefecto).classes("w-full").mark("agregar-nombre")
        self.datos, self.editores = {}, []
        if self.propiedades:
            with ui.row().classes("w-full items-start gap-4"):
                for propiedad in self.propiedades:
                    campoPropiedad(self.datos, propiedad, "agregar", self.editores)
        if self.conTeclas:
            with ui.row().classes("w-full items-center"):
                ui.label("Distribución").classes("font-bold")
                ui.label("presiona teclas para verlas en las miniaturas").classes("text-caption")
                self.ultimaTecla = ui.label("").classes("font-mono ml-auto")
            self.listaDistribuciones = ui.column().classes("w-full gap-2 max-h-80 overflow-auto")
            self.dibujarDistribuciones()
            ayudaDistribuciones(self.dibujarDistribuciones)
        if self.prefijoArchivo:
            with ui.expansion("Avanzado", icon="tune").classes("w-full") as self.avanzado:
                self.archivo = ui.input("Archivo de acciones").classes("w-full").mark("agregar-archivo")
            self.mostrarArchivoPorDefecto()
        with ui.stepper_navigation():
            if self.listarDisponibles:
                ui.button("Atrás", on_click=self.volverABuscar).props("flat")
            else:
                ui.button("Cancelar", on_click=self.dialogo.close).props("flat")
            ui.button("Guardar", icon="save", color=tema.colorOscuro, on_click=self.guardar).mark("agregar-guardar")

    def dibujarDistribuciones(self) -> None:
        """Tarjetas con miniatura; se vuelve a llamar al recargar, por si el usuario agregó una distribución"""
        self.tarjetasDistribucion: dict[str | None, ui.card] = {}
        self.teclasMiniaturas: list[dict[str, list[ui.element]]] = []
        nombres = [None, *distribucionesDisponibles()]
        if self.distribucion not in nombres:
            self.distribucion = None
        self.listaDistribuciones.clear()
        with self.listaDistribuciones:
            for nombreDistribucion in nombres:
                with ui.card().classes("w-full p-2") as tarjeta:
                    tarjeta.mark(f"agregar-distribucion-{nombreDistribucion}")
                    ui.label(nombreDistribucion or "Ninguna (ver como lista)").classes("font-bold")
                    distribucion = cargarDistribucion(nombreDistribucion) if nombreDistribucion else None
                    if distribucion:
                        self.teclasMiniaturas.append(miniatura(distribucion, marca=f"mini-{nombreDistribucion}"))
                tarjetaElegible(tarjeta, lambda n=nombreDistribucion: self.elegirDistribucion(n))
                self.tarjetasDistribucion[nombreDistribucion] = tarjeta
        marcarTarjeta(self.tarjetasDistribucion, self.distribucion)

    def escuchar(self, rutas: list[str], alPresionar) -> None:
        self.dejarDeEscuchar()
        if not self.conTeclas:
            return  # ponytail: el pedal se elige con click; escucharlo para reconocerlo es otra mejora
        self.escuchas = [background_tasks.create(escucharTeclado(ruta, alPresionar)) for ruta in rutas]

    def dejarDeEscuchar(self) -> None:
        for escucha in self.escuchas:
            escucha.cancel()
        self.escuchas = []

    def elegir(self, ruta: str, tecla: str = "") -> None:
        self.ruta = ruta
        marcarTarjeta(self.tarjetasTeclado, ruta)
        if tecla:
            self.teclaTeclado[ruta].text = tecla
        self.botonSiguiente.enable()

    def irAConfigurar(self) -> None:
        # Solo el elegido: sus teclas se iluminan en las miniaturas para reconocer la distribución
        self.escuchar([self.ruta], self.iluminar)
        self.pasos.next()

    def volverABuscar(self) -> None:
        if self.conTeclas:
            self.apagarMiniaturas()
        self.escuchar(list(self.tarjetasTeclado), self.elegir)
        self.pasos.previous()

    def iluminar(self, ruta: str, tecla: str) -> None:
        self.ultimaTecla.text = tecla
        for teclas in self.teclasMiniaturas:
            for div in teclas.get(tecla, []):
                div.classes(add=f"bg-{tema.colorActivo}", remove=f"bg-{tema.colorTeclaVacia}")

    def apagarMiniaturas(self) -> None:
        self.ultimaTecla.text = ""
        for teclas in self.teclasMiniaturas:
            for divs in teclas.values():
                for div in divs:
                    div.classes(add=f"bg-{tema.colorTeclaVacia}", remove=f"bg-{tema.colorActivo}")

    def elegirDistribucion(self, nombreDistribucion: str | None) -> None:
        self.distribucion = nombreDistribucion
        marcarTarjeta(self.tarjetasDistribucion, nombreDistribucion)

    def archivoPorDefecto(self) -> str:
        """<tipo>_<nombre>, ej. teclado_moon_lander: dice de qué es el archivo sin que el usuario lo piense"""
        return "_".join(filter(None, [self.prefijoArchivo, re.sub(r"\W+", "_", (self.nombre.value or "").lower()).strip("_")]))

    def mostrarArchivoPorDefecto(self) -> None:
        if not self.prefijoArchivo:
            return
        # hint y no placeholder: Quasar solo muestra el placeholder con el campo enfocado
        self.archivo.props["hint"] = f"Si lo dejas vacío: {self.archivoPorDefecto()}.md"
        self.archivo.update()

    def guardar(self) -> None:
        nombre = (self.nombre.value or "").strip()
        archivo = None
        if self.prefijoArchivo:
            archivo = (self.archivo.value or "").strip().removesuffix(".md") or self.archivoPorDefecto()
        errorNombre = None
        if not nombre:
            errorNombre = "Falta el nombre"
        elif nombre.lower() in self.nombresUsados:
            errorNombre = f"Ya existe {nombre}"
        # Solo un nombre de archivo, sin carpetas: se crea en el perfil
        errorArchivo = None if archivo is None or re.fullmatch(r"[\w-]+", archivo) else "Solo letras, números, - y _"
        marcarError(self.nombre, errorNombre)
        faltan = [editor for propiedad, editor in self.editores if propiedad.obligatorio and editor.value in (None, "")]
        for _, editor in self.editores:
            marcarError(editor, "Obligatorio" if editor in faltan else None)
        if self.prefijoArchivo:
            marcarError(self.archivo, errorArchivo if nombre else None)
        if errorArchivo and nombre:
            self.avanzado.open()  # el error no se vería con Avanzado cerrado
        if errorNombre or errorArchivo or faltan:
            return
        data = {"nombre": nombre, **self.datos}
        if self.ruta:
            data["dispositivo"] = self.ruta
        if archivo:
            data["archivo"] = archivo
        if self.distribucion:
            data["distribucion"] = self.distribucion
        self.dialogo.close()
        self.alGuardar(data)
