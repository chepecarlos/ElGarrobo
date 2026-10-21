"""Diálogo para elegir la distribución física de un teclado (keyboard-layout-editor.com)"""

from nicegui import ui

from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.editores import encabezado


def medidaDistribucion(distribucion: list[dict]) -> tuple[float, float]:
    """Ancho y alto del teclado en unidades de tecla"""
    ancho = max(t.get("x", 0) + t.get("w", 1) for t in distribucion)
    alto = max(t.get("y", 0) + t.get("h", 1) for t in distribucion)
    return ancho, alto


class dialogoDistribucion:
    """Muestra las distribuciones disponibles con una miniatura; al elegir una se guarda en teclados.md"""

    def __init__(self, alElegir) -> None:
        self.alElegir = alElegir
        "Recibe el dispositivo después de cambiar la distribución, para redibujar su pestaña"
        # Se llena al abrir con las distribuciones disponibles
        with ui.dialog() as self.dialogo, ui.card():
            self.lista = ui.column()

    def abrir(self, dispositivo: dispositivo) -> None:
        from elGarrobo.dispositivos.miteclado.mi_teclado_macro import cargarDistribucion, distribucionesDisponibles, folderDistribucionesUsuario

        def elegir(nombreDistribucion: str | None) -> None:
            dispositivo.cambiarDistribucion(nombreDistribucion)
            self.dialogo.close()
            ui.notify(f"Distribución de {dispositivo.nombre}: {nombreDistribucion or 'ninguna'}")
            self.alElegir(dispositivo)

        unidad = 10
        self.lista.clear()
        with self.lista:
            encabezado(ui.label(f"Distribución de {dispositivo.nombre}").classes("text-lg"), 2)
            ui.label(f"Agrega las tuyas (JSON de keyboard-layout-editor.com) en {folderDistribucionesUsuario()}").classes("text-xs")
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
                        ancho, alto = medidaDistribucion(distribucion)
                        with ui.element("div").classes("relative").style(f"width: {ancho * unidad}px; height: {alto * unidad}px"):
                            for t in distribucion:
                                estilo = f"left: {t.get('x', 0) * unidad}px; top: {t.get('y', 0) * unidad}px; width: {t.get('w', 1) * unidad - 1}px; height: {t.get('h', 1) * unidad - 1}px"
                                ui.element("div").classes(f"absolute bg-{tema.colorTeclaVacia} rounded-sm").style(estilo)
        self.dialogo.open()
