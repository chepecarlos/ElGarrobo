"""Ventana pequeña de Sí / No; en una macro, si se responde No se detienen los pasos siguientes"""

import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import ttk

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion
from .accionListaCheckBox import _obtenerRoot

Logger = ConfigurarLogging(__name__)


def monitorEn(salidaXrandr: str, x: int, y: int) -> tuple[int, int, int, int] | None:
    """(ancho, alto, x, y) del monitor que contiene el punto, según `xrandr --listactivemonitors`"""
    for monitor in re.finditer(r"(\d+)/\d+x(\d+)/\d+\+(\d+)\+(\d+)", salidaXrandr):
        ancho, alto, mx, my = map(int, monitor.groups())
        if mx <= x < mx + ancho and my <= y < my + alto:
            return ancho, alto, mx, my
    return None


def monitorActivo(ventana: tk.Misc) -> tuple[int, int, int, int]:
    """Monitor donde está el mouse; tkinter solo ve el escritorio entero (todos los monitores juntos)"""
    x, y = ventana.winfo_pointerxy()
    try:
        salida = subprocess.run(["xrandr", "--listactivemonitors"], capture_output=True, text=True, timeout=2).stdout
    except (OSError, subprocess.SubprocessError):
        salida = ""
    return monitorEn(salida, x, y) or (ventana.winfo_screenwidth(), ventana.winfo_screenheight(), 0, 0)


def _construirVentana(titulo: str, mensaje: str, tiempo: int, responder) -> None:
    """Crea la ventana de confirmación; se llama desde el hilo de tkinter"""
    ventana = tk.Toplevel(_obtenerRoot())
    # Escondida hasta tener su posición, así el gestor de ventanas no la pone en otro lado
    ventana.withdraw()
    ventana.title(titulo)
    ventana.resizable(False, False)
    ventana.attributes("-topmost", True)
    ventana.configure(bg="#1e1e2e")

    def contestar(valor: bool) -> None:
        responder(valor)
        ventana.destroy()

    marco = ttk.Frame(ventana, padding=(18, 14))
    marco.pack(fill="both", expand=True)
    ttk.Label(marco, text=titulo, style="Titulo.TLabel").pack(anchor="w")
    ttk.Label(marco, text=mensaje, wraplength=340).pack(anchor="w", pady=(6, 12))

    botones = ttk.Frame(marco)
    botones.pack(fill="x")
    ttk.Button(botones, text="No (Esc)", command=lambda: contestar(False)).pack(side="right")
    ttk.Button(botones, text="Sí (Enter)", style="Accent.TButton", command=lambda: contestar(True)).pack(
        side="right", padx=(0, 8)
    )

    ventana.bind("<Return>", lambda _: contestar(True))
    ventana.bind("<KP_Enter>", lambda _: contestar(True))
    ventana.bind("<Escape>", lambda _: contestar(False))
    ventana.protocol("WM_DELETE_WINDOW", lambda: contestar(False))
    ventana.after(tiempo * 1000, lambda: contestar(False))

    # Centrada en el monitor del mouse y con el foco, para responder con el teclado
    ventana.update_idletasks()
    ancho, alto, mx, my = monitorActivo(ventana)
    x = mx + (ancho - ventana.winfo_reqwidth()) // 2
    y = my + (alto - ventana.winfo_reqheight()) // 2
    ventana.geometry(f"+{x}+{y}")
    ventana.deiconify()
    ventana.focus_force()


class accionConfirmar(accion):
    """Pregunta Sí / No; en una macro, No detiene los pasos siguientes"""

    nombre = "Confirmar"
    comando = "confirmar"
    categoria = "Macros y datos"
    descripcion = "Pregunta Sí / No en una ventana pequeña; en una macro, si se responde No no sigue con los demás pasos"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.agregarPropiedad(
            propiedadAccion(
                nombre="Mensaje",
                atributo="mensaje",
                tipo=[str],
                descripcion="Pregunta que se muestra",
                ejemplo="¿Cancelar la impresión de la MK4s?",
                defecto="¿Continuar?",
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Título",
                atributo="titulo",
                tipo=[str],
                descripcion="Título de la ventana",
                ejemplo="Confirmar",
                defecto="Confirmar",
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Tiempo",
                atributo="tiempo",
                tipo=[int],
                descripcion="Segundos para responder, si no se responde cuenta como No",
                defecto=30,
            )
        )

    def ejecutar(self) -> bool:
        """True solo si se respondió Sí; sin ventana posible es No, para no hacer la acción a ciegas"""
        return self.sePuedeEjecutar() and self.preguntar()

    def preguntar(self) -> bool:
        """Muestra la ventana y espera la respuesta (bloquea el hilo que ejecuta la macro)"""
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            Logger.warning("Confirmar[Error] No hay entorno gráfico, se toma como No")
            return False

        mensaje = str(self.obtenerValor("mensaje"))
        titulo = str(self.obtenerValor("titulo"))
        tiempo = max(1, int(self.obtenerValor("tiempo")))
        respuesta: list[bool] = []
        listo = threading.Event()

        def responder(valor: bool) -> None:
            # Solo la primera: Enter y el tiempo pueden llegar casi juntos
            if not listo.is_set():
                respuesta.append(valor)
                listo.set()

        try:
            _obtenerRoot().after(0, lambda: _construirVentana(titulo, mensaje, tiempo, responder))
        except Exception as error:
            Logger.error(f"Confirmar[Error] No se pudo abrir la ventana: {error}")
            return False

        # Margen por si el hilo de tkinter murió y la ventana nunca contesta
        listo.wait(tiempo + 5)
        aceptado = bool(respuesta and respuesta[0])
        Logger.info(f"Confirmar[{'Sí' if aceptado else 'No'}] {mensaje}")
        return aceptado
