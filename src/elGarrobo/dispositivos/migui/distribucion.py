"""Diálogo para elegir la distribución física de un teclado (keyboard-layout-editor.com)"""

import html

from nicegui import ui

from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.editores import encabezado


def medidaDistribucion(distribucion: list[dict]) -> tuple[float, float]:
    """Ancho y alto del teclado en unidades de tecla"""
    ancho = max(t.get("x", 0) + t.get("w", 1) for t in distribucion)
    alto = max(t.get("y", 0) + t.get("h", 1) for t in distribucion)
    return ancho, alto


def miniatura(distribucion: list[dict], unidad: int = 10, marca: str | None = None) -> dict[str, list[ui.element]]:
    """Dibuja el teclado en pequeño; devuelve keycode → divs de esa tecla, para iluminarlas

    Args:
        marca (str): si se da, cada tecla se marca como "<marca>-<keycode>" (para los tests)
    """
    teclas: dict[str, list[ui.element]] = {}
    ancho, alto = medidaDistribucion(distribucion)
    with ui.element("div").classes("relative").style(f"width: {ancho * unidad}px; height: {alto * unidad}px"):
        for t in distribucion:
            estilo = (
                f"left: {t.get('x', 0) * unidad}px; top: {t.get('y', 0) * unidad}px; "
                f"width: {t.get('w', 1) * unidad - 1}px; height: {t.get('h', 1) * unidad - 1}px"
            )
            tecla = ui.element("div").classes(f"absolute bg-{tema.colorTeclaVacia} rounded-sm").style(estilo)
            if marca:
                tecla.mark(f"{marca}-{t['key']}")
            teclas.setdefault(t["key"], []).append(tecla)
    return teclas


def ayudaDistribuciones(alRecargar=None) -> None:
    """Cómo agregar una distribución propia cuando la del teclado no está

    Args:
        alRecargar: si se da, muestra un botón para volver a leer las distribuciones sin cerrar el diálogo
    """
    from elGarrobo.dispositivos.miteclado.mi_teclado_macro import folderDistribucionesUsuario

    folder = folderDistribucionesUsuario()
    folder.mkdir(parents=True, exist_ok=True)  # que exista cuando el usuario la busque
    with ui.row().classes("w-full items-start no-wrap gap-2"):
        # Cerrada: la explicación es larga y solo la necesita quien no encuentra su distribución
        with ui.expansion("¿No está tu teclado?", icon="help_outline").classes("grow text-caption").props("dense"):
            # html y no markdown: el enlace debe abrir otra pestaña, no sacar al usuario de la GUI
            ui.html(
                "Dibújalo en "
                '<a href="https://www.keyboard-layout-editor.com" target="_blank" rel="noopener" class="texto-acento">'
                "keyboard-layout-editor.com</a>, descárgalo con <i>Download JSON</i> y guárdalo en "
                f"<code>{html.escape(str(folder))}</code>. Las teclas se reconocen por su texto (Q, F1, Shift…); "
                "en las especiales escribe el código que aparece al presionarlas, ej. <code>KEY_F13</code>.",
                sanitize=False,
            ).classes("text-caption px-4 pb-2")
        if alRecargar:
            boton = ui.button(icon="refresh", on_click=alRecargar).props("flat round dense")
            boton.props["aria-label"] = "Recargar distribuciones"
            boton.tooltip("Recargar distribuciones").mark("recargar-distribuciones")


class dialogoDistribucion:
    """Muestra las distribuciones disponibles con una miniatura; al elegir una se guarda en teclados.md"""

    def __init__(self, alElegir) -> None:
        self.alElegir = alElegir
        "Recibe el dispositivo después de cambiar la distribución, para redibujar su pestaña"
        # Se llena al abrir con las distribuciones disponibles
        with ui.dialog() as self.dialogo, ui.card():
            self.lista = ui.column()

    def abrir(self, dispositivo: dispositivo) -> None:
        from elGarrobo.dispositivos.miteclado.mi_teclado_macro import cargarDistribucion, distribucionesDisponibles

        def elegir(nombreDistribucion: str | None) -> None:
            dispositivo.cambiarDistribucion(nombreDistribucion)
            self.dialogo.close()
            ui.notify(f"Distribución de {dispositivo.nombre}: {nombreDistribucion or 'ninguna'}")
            self.alElegir(dispositivo)

        self.lista.clear()
        with self.lista:
            encabezado(ui.label(f"Distribución de {dispositivo.nombre}").classes("text-lg"), 2)
            ayudaDistribuciones()
            for nombreDistribucion in [None, *distribucionesDisponibles()]:
                actual = nombreDistribucion == dispositivo.distribucion
                with ui.card().classes(f"w-full cursor-pointer opcion-distribucion {f'border-2 border-{tema.colorActivo}' if actual else ''}") as tarjeta:
                    tarjeta.props(f"tabindex=0 role=button aria-pressed={str(actual).lower()}")
                    for evento in ("click", "keydown.enter", "keydown.space"):
                        tarjeta.on(evento, lambda n=nombreDistribucion: elegir(n))
                    tarjeta.mark(f"opcionDistribucion-{nombreDistribucion}")
                    ui.label(nombreDistribucion or "Ninguna (ver como lista)").classes("font-bold")
                    distribucion = cargarDistribucion(nombreDistribucion) if nombreDistribucion else None
                    if distribucion:
                        miniatura(distribucion)
        self.dialogo.open()
