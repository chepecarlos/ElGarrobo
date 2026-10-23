"""Diálogos de confirmación de la GUI"""

from nicegui import ui

from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.editores import encabezado


def crearDialogoConfirmacion(mensaje: str, textoBoton: str, accionConfirmada) -> ui.dialog:
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

            ui.button(textoBoton, color=tema.colorPeligro, on_click=confirmar).props("unelevated")
    return dialogo


def crearDialogoReiniciar(obtenerPendientes, alConfirmar) -> callable:
    """Crea (sin abrir) el diálogo de reiniciar; devuelve la función que lo abre con los pendientes del momento

    Los cambios pendientes son la razón de reiniciar: se listan aquí porque el tooltip del botón de la cabecera
    no se ve en el celular ni con el teclado. Reiniciar no es peligroso como Salir, por eso no va en rojo: con
    cambios va en ámbar como el botón que lo abrió, sin ellos (desde el menú) en el color de los botones

    Args:
        obtenerPendientes: devuelve el dict clave → descripción de los cambios que esperan reinicio
        alConfirmar: reinicia ElGarrobo
    """
    with ui.dialog() as dialogo, ui.card().classes("max-w-md"):

        @ui.refreshable
        def contenido() -> None:
            pendientes = list(obtenerPendientes().values())
            encabezado(ui.label("¿Reiniciar ElGarrobo?").classes("text-h6"), 2)
            if pendientes:
                ui.label("Se aplicarán estos cambios:")
                # list-disc: Tailwind quita las viñetas de ul
                with ui.element("ul").classes("list-disc pl-6").mark("reiniciar-pendientes"):
                    for pendiente in pendientes:
                        with ui.element("li"):
                            ui.label(pendiente)
            ui.label("Las teclas no responden unos segundos mientras arranca.").classes("text-caption")
            with ui.row().classes("w-full justify-end"):
                ui.button("Cancelar", on_click=dialogo.close).props("flat no-caps")

                def confirmar() -> None:
                    dialogo.close()
                    alConfirmar()

                boton = ui.button("Reiniciar ahora", icon="restart_alt", on_click=confirmar).props("unelevated no-caps")
                if pendientes:
                    boton.props(f"color={tema.colorPendiente} text-color=black")
                else:
                    boton.props(f"color={tema.colorOscuro}")

        contenido()

    def abrir() -> None:
        contenido.refresh()
        dialogo.open()

    return abrir


class dialogoPregunta:
    """Diálogo de confirmación con mensaje variable (crearDialogoConfirmacion es para mensajes fijos)"""

    def __init__(self) -> None:
        self.funcion = None
        "Lo que se ejecuta al confirmar"
        with ui.dialog() as self.dialogo, ui.card():
            self.texto = ui.label("")
            with ui.row():
                ui.button("Cancelar", on_click=self.dialogo.close).props("flat")
                self.boton = ui.button("", color=tema.colorPeligro, on_click=self.confirmar).props("unelevated").mark("botonConfirmarPregunta")

    def preguntar(self, mensaje: str, textoBoton: str, funcion) -> None:
        self.texto.text = mensaje
        self.boton.text = textoBoton
        self.funcion = funcion
        self.dialogo.open()

    def confirmar(self) -> None:
        self.dialogo.close()
        self.funcion()
