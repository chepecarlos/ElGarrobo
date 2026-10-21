"""Diálogo de propiedades del folder: valores por defecto de los botones del folder actual (propiedad_folder)"""

from nicegui import ui

from elGarrobo.dispositivos.dataAccion import dataAccion
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.migui import tema
from elGarrobo.dispositivos.migui.editores import encabezado


def usaCuadriculaFolder(aparato: dispositivo) -> bool:
    """Dispositivos sin botones físicos (MQTT, GUI): su cuadrícula sale de la propiedad_folder"""
    # Los teclados no: eligen una distribución
    return type(aparato).gruposBotones is dispositivo.gruposBotones and not hasattr(aparato, "cambiarDistribucion")


class dialogoFolder:
    """Edita la propiedad_folder del folder actual de un dispositivo; la crea si no existe y la quita si queda vacía"""

    def __init__(self, alGuardar) -> None:
        self.alGuardar = alGuardar
        "Recibe el dispositivo después de guardar, para redibujar su pestaña"
        self.dispositivo: dispositivo = None
        "Dispositivo cuyas propiedades del folder se están editando"
        with ui.dialog() as self.dialogo, ui.card():
            encabezado(ui.label("Apariencia del folder").classes("text-lg"), 2)
            ui.label("Valores por defecto de los botones de este folder").classes("text-xs")
            self.fondo = ui.color_input("Fondo", preview=True).classes("w-64").mark("editor-folder-fondo")
            self.tamaño = ui.number("Tamaño máximo del título", min=1, precision=0).classes("w-64").mark("editor-folder-tamanno")
            # Solo dispositivos sin botones físicos (MQTT, GUI): se dibujan con esta cuadrícula
            with ui.row().classes("w-64 no-wrap") as self.filaCuadricula:
                self.columnas = ui.number("Columnas", min=1, precision=0).classes("flex-1").mark("editor-folder-columnas")
                self.filas = ui.number("Filas", min=1, precision=0).classes("flex-1").mark("editor-folder-filas")
            ui.button("Guardar", color=tema.colorOscuro, on_click=self.guardar).mark("botonGuardarFolder")

    def abrir(self, dispositivo: dispositivo) -> None:
        """Carga en el diálogo la propiedad_folder del folder actual del dispositivo"""
        self.dispositivo = dispositivo
        propiedad = dispositivo.propiedadFolder
        self.fondo.value = (propiedad.fondo if propiedad else None) or ""
        self.tamaño.value = propiedad.tituloOpciones.get("tamanno_maximo") if propiedad else None
        self.filaCuadricula.visible = usaCuadriculaFolder(dispositivo)
        columnas, filas = dispositivo.cuadriculaFolder() or (None, None)
        self.columnas.value = columnas
        self.filas.value = filas
        self.dialogo.open()

    def guardar(self) -> None:
        """Guarda la propiedad_folder; la crea si no existe y la quita si queda vacía"""
        dispositivo = self.dispositivo
        propiedad = dispositivo.propiedadFolder
        if propiedad is None:
            propiedad = dataAccion(key="propiedad_folder")
            dispositivo.listaAcciones.append(propiedad)

        propiedad.fondo = self.fondo.value or None
        tamaño = self.tamaño.value
        if tamaño:
            propiedad.tituloOpciones["tamanno_maximo"] = int(tamaño)
        else:
            propiedad.tituloOpciones.pop("tamanno_maximo", None)
        if self.filaCuadricula.visible:
            columnas, filas = self.columnas.value, self.filas.value
            if columnas and filas:
                propiedad.extra["cuadricula"] = {"columnas": int(columnas), "filas": int(filas)}
            else:
                propiedad.extra.pop("cuadricula", None)

        if propiedad.aDict() == {"key": "propiedad_folder"}:
            dispositivo.listaAcciones.remove(propiedad)

        dispositivo.salvarAcciones()
        self.dialogo.close()
        ui.notify(f"Apariencia del folder guardada en {dispositivo.nombre}")
        self.alGuardar(dispositivo)
