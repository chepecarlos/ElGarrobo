"""Acción para ejecutar comando de terminal (OS)"""

import os
import subprocess

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion

logger = ConfigurarLogging(__name__)


class accionOS(accion):
    """Ejecuta comando de terminal"""

    nombre = "Comando OS"
    comando = "os"
    descripcion = "Ejecuta comando de terminal"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadComando = {
            "nombre": "Comando",
            "tipo": str,
            "obligatorio": True,
            "atributo": "comando",
            "descripcion": "comando de bash",
            "ejemplo": "ls",
        }

        self.agregarPropiedad(propiedadComando)

        self.funcion = self.ejecutrarComando

    def ejecutrarComando(self):
        """Ejecuta comando en terminal"""
        comando: str = self.obtenerValor("comando")

        logger.info(f"OS[{comando}]")
        respuesta = subprocess.run(
            comando,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
        )

        if respuesta.stdout:
            print("Salida estándar:", (respuesta.stdout or "").rstrip(), ";")
        if respuesta.stderr:
            print("Error estándar:", (respuesta.stderr or "").rstrip(), ";")
        if respuesta.returncode != 0:
            print("Código de retorno:", respuesta.returncode)
