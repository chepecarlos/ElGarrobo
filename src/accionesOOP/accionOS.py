from .accionBase import accionBase
import os

from MiLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


class accionOS(accionBase):
    def __init__(self) -> None:
        nombre = "Comando OS"
        comando = "os"
        descripcion = "Ejecuta comando de terminal"
        super().__init__(nombre, comando, descripcion)

        propiedadTiempo = {
            "nombre": "Comando",
            "tipo": str,
            "obligatorio": True,
            "atributo": "comando",
            "descripcion": "comando de bash",
            "ejemplo": "ls",
        }

        self.agregarPropiedad(propiedadTiempo)

        self.funcion = self.ejecutrarComando

    def ejecutrarComando(self):
        """Ejecuta comando en terminal"""
        comando = self.obtenerValor("comando")
        logger.info(f"OS[{comando}]")
        os.system(comando)
