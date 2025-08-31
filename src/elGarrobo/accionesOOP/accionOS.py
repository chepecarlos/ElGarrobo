"""Acción para ejecutar comando de terminal (OS)"""

import os
import subprocess

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

logger = ConfigurarLogging(__name__)


class accionOS(accionBase):
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
        comando = self.obtenerValor("comando")
        logger.info(f"OS[{comando}]")
        respuesta = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = respuesta.communicate()

        # Imprimir la salida
        print("Salida estándar:", stdout.decode(), ";")

        # Imprimir errores
        print("Error estándar:", stderr.decode(), ";")
        # version =  return.read()
        return_code = respuesta.wait()
        print(f"Versión del comando: {respuesta}")

        print("Código de retorno:", return_code)

        # respuesta = os.system(comando)
        # print(f"Respuesta del comando: {respuesta}")
