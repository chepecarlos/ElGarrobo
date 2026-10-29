"""Panel para encontrar acciones: agrupadas por categoría con su descripción, incluidas las de módulos apagados"""

from dataclasses import dataclass

from nicegui import ui

from elGarrobo.dispositivos.migui.editores import encabezado, nombrar


@dataclass
class acciónCatálogo:
    categoria: str
    nombre: str
    comando: str
    descripcion: str
    moduloApagado: str = ""
    "Nombre del módulo que hay que activar para usarla, vacío si está disponible"


def listarAcciones(listaClasesAcciones: dict) -> list[acciónCatálogo]:
    """Acciones registradas ordenadas por categoría y nombre, al final las de módulos apagados"""
    # Al usarse y no arriba, igual que /modulos en migui.py
    from elGarrobo.modulos import cargarModulos

    acciones = []
    moduloDe = {}
    for claseModulo in cargarModulos():
        for claseAcción in claseModulo.acciones:
            moduloDe[claseAcción.comando] = claseModulo.nombre
            if claseAcción.comando not in listaClasesAcciones:
                objeto = claseAcción()
                acciones.append(
                    acciónCatálogo(
                        claseModulo.nombre, objeto.nombre, objeto.comando, objeto.descripcion, claseModulo.nombre
                    )
                )
    for comando, claseAcción in listaClasesAcciones.items():
        objeto = claseAcción()
        acciones.append(
            acciónCatálogo(moduloDe.get(comando, objeto.categoria), objeto.nombre, comando, objeto.descripcion)
        )
    return sorted(acciones, key=lambda a: (bool(a.moduloApagado), a.categoria, a.nombre))


class catalogoAcciones:
    """Diálogo con todas las acciones; al elegir una la pone en el selector desde el que se abrió

    Se crea una vez al armar la página y cada selector lo abre con el botón de `agregarBoton`
    """

    def __init__(self, listaClasesAcciones: dict) -> None:
        self.listaClasesAcciones = listaClasesAcciones
        self.selector: ui.select = None
        "Selector que abrió el panel"
        with ui.dialog() as self.dialogo, ui.card().classes("w-full max-w-3xl"):
            encabezado(ui.label("Acciones disponibles").classes("text-lg"), 2)
            self.buscador = (
                ui.input("Buscar por nombre o qué hace", on_change=self.dibujar)
                .props("clearable autofocus")
                .classes("w-full")
                .mark("catalogo-buscar")
            )
            self.lista = ui.column().classes("w-full gap-0")
            ui.button("Cerrar", on_click=self.dialogo.close).props("flat")
        # Se dibuja al abrir: cerrado no deja etiquetas con los nombres de las acciones repetidas en la página
        self.dialogo.on("hide", self.lista.clear)

    def agregarBoton(self, selector: ui.select) -> None:
        """Pone a la derecha del selector el botón que abre el panel"""
        with selector.add_slot("after"):
            nombrar(
                ui.button(icon="menu_book", on_click=lambda: self.abrir(selector))
                .props("flat round")
                .mark("botonCatalogo"),
                "Ver todas las acciones",
            )

    def abrir(self, selector: ui.select) -> None:
        self.selector = selector
        self.buscador.value = ""
        self.dibujar()
        self.dialogo.open()

    def dibujar(self) -> None:
        texto = (self.buscador.value or "").lower()
        acciones = [
            a
            for a in listarAcciones(self.listaClasesAcciones)
            if texto in f"{a.nombre} {a.comando} {a.descripcion}".lower()
        ]
        self.lista.clear()
        with self.lista:
            if not acciones:
                ui.label("Ninguna acción coincide").classes("text-caption")
            categoria = None
            for acción in acciones:
                if acción.categoria != categoria:
                    categoria = acción.categoria
                    encabezado(ui.label(categoria).classes("texto-acento text-bold mt-3"), 3)
                    grupo = ui.list().props("dense separator").classes("w-full")
                with grupo:
                    disponible = not acción.moduloApagado
                    # Sin on_click no es clickable: la de un módulo apagado se ve pero no se elige
                    with ui.item(
                        on_click=(lambda nombre=acción.nombre: self.elegir(nombre)) if disponible else None
                    ).mark(f"catalogo-{acción.comando}"):
                        with ui.item_section().classes("" if disponible else "opacity-60"):
                            ui.item_label(acción.nombre)
                            ui.item_label(acción.descripcion).props("caption")
                        with ui.item_section().props("side"):
                            ui.item_label(acción.comando).props("caption")
                    if not disponible:
                        ui.label(f"Activa el módulo {acción.moduloApagado} en Módulos para usarla").classes(
                            "texto-aviso text-caption px-4 pb-1"
                        )

    def elegir(self, nombre: str) -> None:
        self.selector.value = nombre
        self.dialogo.close()
