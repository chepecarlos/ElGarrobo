"""Diálogos de confirmación de la GUI"""

from nicegui import ui

from elGarrobo.dispositivos.migui import tema


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
