"""Acción para mostrar una lista de tareas con checkboxes"""

import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

# from .heramientas.propiedadAccion import propiedadAccion

Logger = ConfigurarLogging(__name__)


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
        """Muestra una ventana nativa pequeña con Tkinter."""
        display = os.environ.get("DISPLAY")
        wayland_display = os.environ.get("WAYLAND_DISPLAY")
        Logger.info(f"ListaCheckBox[Entorno] DISPLAY={display} WAYLAND_DISPLAY={wayland_display}")

        if not display and not wayland_display:
            Logger.warning("ListaCheckBox[Error] No hay entorno gráfico local para mostrar la ventana")
            return False

        def abrirVentana():
            try:
                ventana = tk.Tk()
                ventana.title(titulo)
                ventana.geometry("420x320")
                ventana.resizable(False, False)
                ventana.attributes("-topmost", True)

                marco = ttk.Frame(ventana, padding=12)
                marco.pack(fill="both", expand=True)

                ttk.Label(marco, text=titulo, font=("Arial", 12, "bold")).pack(anchor="w")
                ttk.Label(marco, text="Marca las tareas completadas").pack(anchor="w", pady=(0, 8))

                resumen = tk.StringVar(value=f"0/{len(tareas)} tareas marcadas")
                ttk.Label(marco, textvariable=resumen).pack(anchor="w", pady=(0, 8))

                estados = {}

                def actualizarResumen() -> None:
                    completadas = sum(variable.get() for variable in estados.values())
                    resumen.set(f"{completadas}/{len(tareas)} tareas marcadas")

                lista = ttk.Frame(marco)
                lista.pack(fill="both", expand=True)

                if tareas:
                    for tarea in tareas:
                        variable = tk.BooleanVar(value=False)
                        estados[tarea] = variable
                        ttk.Checkbutton(lista, text=tarea, variable=variable, command=actualizarResumen).pack(anchor="w")
                else:
                    ttk.Label(lista, text="No hay tareas configuradas").pack(anchor="w")

                def limpiarSeleccion() -> None:
                    for variable in estados.values():
                        variable.set(False)
                    actualizarResumen()

                def mostrarSeleccion() -> None:
                    seleccionadas = [tarea for tarea, variable in estados.items() if variable.get()]
                    mensaje = ", ".join(seleccionadas) if seleccionadas else "No hay tareas seleccionadas"
                    messagebox.showinfo(titulo, mensaje)

                botones = ttk.Frame(marco)
                botones.pack(fill="x", pady=(10, 0))
                ttk.Button(botones, text="Mostrar", command=mostrarSeleccion).pack(side="left", padx=(0, 6))
                ttk.Button(botones, text="Limpiar", command=limpiarSeleccion).pack(side="left")
                ttk.Button(botones, text="Cerrar", command=ventana.destroy).pack(side="right")

                ventana.mainloop()
            except Exception as error:
                Logger.error(f"ListaCheckBox[Error] Ventana local: {error}")

        threading.Thread(target=abrirVentana, daemon=True, name="ListaCheckBoxTk").start()
        Logger.info(f"ListaCheckBox[VentanaLocal] {titulo} - {len(tareas)} tareas")
        return True

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
