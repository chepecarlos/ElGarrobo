"""Acción para mostrar una lista de tareas con checkboxes"""

import os
import threading
import tkinter as tk
from tkinter import ttk

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)

_ANCHO = 440
_ALTO_MIN = 200
_ALTO_MAX = 520
_ALTO_ITEM = 28
_ALTO_CABECERA = 110
_ALTO_BOTONES = 80

# Root compartido: un solo hilo de tkinter, múltiples Toplevel
_tk_root: tk.Tk | None = None
_tk_lock = threading.Lock()


def _obtenerRoot() -> tk.Tk:
    """Devuelve el root oculto compartido, creándolo si no existe."""
    global _tk_root
    with _tk_lock:
        try:
            if _tk_root is not None and _tk_root.winfo_exists():
                return _tk_root
        except Exception:
            pass

        listo = threading.Event()

        def _iniciarLoop():
            global _tk_root
            root = tk.Tk()
            root.withdraw()
            _configurarEstilo(ttk.Style(root))
            _tk_root = root
            listo.set()
            root.mainloop()

        threading.Thread(target=_iniciarLoop, daemon=True, name="TkRootLoop").start()
        listo.wait(timeout=5)

    return _tk_root


def _configurarEstilo(style: ttk.Style) -> None:
    style.theme_use("clam")
    style.configure("TFrame", background="#1e1e2e")
    style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
    style.configure("Titulo.TLabel", background="#1e1e2e", foreground="#cba6f7", font=("Segoe UI", 13, "bold"))
    style.configure("Resumen.TLabel", background="#1e1e2e", foreground="#a6e3a1", font=("Segoe UI", 9))
    style.configure(
        "TCheckbutton",
        background="#1e1e2e",
        foreground="#cdd6f4",
        font=("Segoe UI", 10),
        focuscolor="#1e1e2e",
    )
    style.map("TCheckbutton", background=[("active", "#313244")], foreground=[("active", "#cba6f7")])
    style.configure("TButton", background="#313244", foreground="#cdd6f4", font=("Segoe UI", 9), padding=5)
    style.map("TButton", background=[("active", "#45475a")])
    style.configure("Accent.TButton", background="#cba6f7", foreground="#1e1e2e", font=("Segoe UI", 9, "bold"))
    style.map("Accent.TButton", background=[("active", "#b4befe")])
    style.configure("TProgressbar", troughcolor="#313244", background="#a6e3a1", thickness=6)
    style.configure("TScrollbar", background="#313244", troughcolor="#1e1e2e", arrowcolor="#cdd6f4")


def _construirVentana(titulo: str, tareas: list[str]) -> None:
    """Crea un Toplevel con la lista de checkboxes. Debe llamarse desde el hilo de tkinter."""
    root = _tk_root
    alto = min(_ALTO_MAX, _ALTO_CABECERA + len(tareas) * _ALTO_ITEM + _ALTO_BOTONES)
    alto = max(_ALTO_MIN, alto)

    ventana = tk.Toplevel(root)
    ventana.title(titulo)
    ventana.geometry(f"{_ANCHO}x{alto}")
    ventana.minsize(_ANCHO, _ALTO_MIN)
    ventana.maxsize(_ANCHO * 2, _ALTO_MAX + 200)
    ventana.resizable(True, True)
    ventana.attributes("-topmost", True)
    ventana.configure(bg="#1e1e2e")

    marco = ttk.Frame(ventana, padding=(14, 12, 14, 8))
    marco.pack(fill="both", expand=True)
    marco.columnconfigure(0, weight=1)
    marco.rowconfigure(3, weight=1)

    ttk.Label(marco, text=titulo, style="Titulo.TLabel").grid(row=0, column=0, sticky="w")

    resumen_var = tk.StringVar(value=f"0 / {len(tareas)} completadas")
    ttk.Label(marco, textvariable=resumen_var, style="Resumen.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

    progreso_var = tk.DoubleVar(value=0)
    barra = ttk.Progressbar(marco, variable=progreso_var, maximum=max(len(tareas), 1), style="TProgressbar")
    barra.grid(row=2, column=0, sticky="ew", pady=(6, 8))

    contenedor = ttk.Frame(marco)
    contenedor.grid(row=3, column=0, sticky="nsew")
    contenedor.columnconfigure(0, weight=1)
    contenedor.rowconfigure(0, weight=1)

    canvas = tk.Canvas(contenedor, bg="#1e1e2e", highlightthickness=0)
    scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=0, column=0, sticky="nsew")

    lista_frame = ttk.Frame(canvas)
    ventana_id = canvas.create_window((0, 0), window=lista_frame, anchor="nw")

    def ajustarCanvas(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(ventana_id, width=canvas.winfo_width())
        if lista_frame.winfo_reqheight() > canvas.winfo_height():
            scrollbar.grid(row=0, column=1, sticky="ns")
        else:
            scrollbar.grid_remove()

    lista_frame.bind("<Configure>", ajustarCanvas)
    canvas.bind("<Configure>", ajustarCanvas)

    # scroll con rueda solo sobre esta ventana (no contamina otras abiertas)
    def scroll_mouse(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<MouseWheel>", scroll_mouse)
    canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
    lista_frame.bind("<MouseWheel>", scroll_mouse)
    lista_frame.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    lista_frame.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    estados: dict[str, tk.BooleanVar] = {}

    def actualizarResumen() -> None:
        completadas = sum(v.get() for v in estados.values())
        total = len(tareas)
        resumen_var.set(f"{completadas} / {total} completadas")
        progreso_var.set(completadas)
        btn_toggle.configure(text="Limpiar todo" if completadas == total and total > 0 else "Marcar todo")

    for tarea in tareas:
        fila = ttk.Frame(lista_frame, padding=(0, 1))
        fila.pack(fill="x")
        variable = tk.BooleanVar(value=False)
        estados[tarea] = variable
        cb = ttk.Checkbutton(fila, text=tarea, variable=variable, command=actualizarResumen)
        cb.pack(anchor="w", padx=4)
        cb.bind("<MouseWheel>", scroll_mouse)
        cb.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        cb.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    def toggleTodo() -> None:
        completadas = sum(v.get() for v in estados.values())
        nuevo_estado = completadas < len(tareas)
        for v in estados.values():
            v.set(nuevo_estado)
        actualizarResumen()

    separador = ttk.Frame(marco, height=1)
    separador.grid(row=4, column=0, sticky="ew", pady=(8, 0))

    botones = ttk.Frame(marco)
    botones.grid(row=5, column=0, sticky="ew", pady=(6, 0))

    btn_toggle = ttk.Button(botones, text="Marcar todo", command=toggleTodo, style="Accent.TButton")
    btn_toggle.pack(side="left", padx=(0, 6))
    ttk.Button(botones, text="Cerrar", command=ventana.destroy).pack(side="right")


class accionListaCheckBox(accion):
    """Acción para manejar una lista de checkboxes"""

    nombre = "ListaCheckBox"
    comando = "lista_checkbox"
    descripcion = "Maneja una lista de checkboxes"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadTitulo = propiedadAccion(
            nombre="Titulo de la Lista",
            atributo="titulo",
            tipo=[str],
            obligatorio=True,
            descripcion="Título de la lista de tareas",
            ejemplo="Mi Lista de Tareas",
        )

        propiedadListaTareas = propiedadAccion(
            nombre="Lista de Tareas",
            atributo="tareas",
            tipo=[list],
            obligatorio=True,
            descripcion="Lista de tareas a manejar",
            ejemplo='["Tarea 1", "Tarea 2"]',
        )

        self.agregarPropiedad(propiedadTitulo)
        self.agregarPropiedad(propiedadListaTareas)

        self.funcion = self.ventanaListaCheckBox

    def mostrarVentanaLocal(self, titulo: str, tareas: list[str]) -> bool:
        """Solicita al hilo de tkinter que abra un nuevo Toplevel."""
        display = os.environ.get("DISPLAY")
        wayland_display = os.environ.get("WAYLAND_DISPLAY")
        Logger.info(f"ListaCheckBox[Entorno] DISPLAY={display} WAYLAND_DISPLAY={wayland_display}")

        if not display and not wayland_display:
            Logger.warning("ListaCheckBox[Error] No hay entorno gráfico local para mostrar la ventana")
            return False

        try:
            root = _obtenerRoot()
            # after() encola la creación en el hilo de tkinter de forma thread-safe
            root.after(0, lambda: _construirVentana(titulo, tareas))
            Logger.info(f"ListaCheckBox[VentanaLocal] {titulo} - {len(tareas)} tareas")
            return True
        except Exception as error:
            Logger.error(f"ListaCheckBox[Error] No se pudo crear la ventana: {error}")
            return False

    def ventanaListaCheckBox(self):
        """Muestra una ventana pequeña nativa con una lista de tareas."""
        titulo = str(self.obtenerValor("titulo", "Lista de tareas"))
        tareas = self.obtenerValor("tareas", [])

        Logger.info(f"ListaCheckBox[Datos] Titulo: {titulo}, Tareas: {tareas}")

        if not isinstance(tareas, list):
            Logger.error("ListaCheckBox[Error] 'tareas' debe ser una lista")
            return

        tareas = [str(tarea).strip() for tarea in tareas if str(tarea).strip()]

        if not self.mostrarVentanaLocal(titulo, tareas):
            Logger.warning("ListaCheckBox[Error] No se pudo abrir la ventana nativa")
