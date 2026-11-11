"""Ventana para que el usuario escriba un texto; en una secuencia la respuesta pasa al cajón"""

import pyautogui

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionVentanaTexto(accion):
    """Pide un texto en una ventana y lo devuelve"""

    nombre = "Ventana Texto"
    comando = "ventana_texto"
    categoria = "Secuencias y datos"
    descripcion = "Pide un texto en una ventana; en una secuencia guarda la respuesta con secuencia_opciones.respuesta"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.agregarPropiedad(
            propiedadAccion(
                nombre="Mensaje",
                atributo="mensaje",
                tipo=[str],
                descripcion="Pregunta que se muestra",
                ejemplo="¿De qué trata el clip?",
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Título",
                atributo="titulo",
                tipo=[str],
                descripcion="Título de la ventana",
                ejemplo="Clip",
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Por defecto",
                atributo="default",
                tipo=[str],
                descripcion="Texto que aparece ya escrito",
                ejemplo="0:0:0",
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Ocultar",
                atributo="ocultar",
                tipo=[bool],
                descripcion="Muestra * en vez del texto, para contraseñas",
                defecto=False,
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Tipo",
                atributo="tipo",
                tipo=[str],
                descripcion="Tipo de la respuesta",
                defecto="string",
                sugerencias=["string", "entero"],
            )
        )

    def ejecutar(self) -> str | int | None:
        """Devuelve lo escrito (None si se cancela) para que la secuencia lo guarde en el cajón"""
        if not self.sePuedeEjecutar():
            return None

        mensaje = self.obtenerValor("mensaje", "")
        titulo = self.obtenerValor("titulo", "")
        defecto = self.obtenerValor("default", "")

        if self.obtenerValor("ocultar"):
            respuesta = pyautogui.password(mensaje, titulo, defecto, "*")
        else:
            respuesta = pyautogui.prompt(mensaje, titulo, defecto)

        if respuesta and self.obtenerValor("tipo") == "entero":
            respuesta = int(respuesta)

        Logger.info(f"Respuesta[{respuesta if respuesta else 'vacío'}]")
        return respuesta
