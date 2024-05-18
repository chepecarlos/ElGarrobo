from .accionBase import accionBase
import requests

from elGarrobo.miLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


class accionPost(accionBase):
    def __init__(self) -> None:
        nombre = "Post"
        comando = "post"
        descripcion = "Realiza un consulta post para usar API"
        super().__init__(nombre, comando, descripcion)

        propiedadURL = {
            "nombre": "url",
            "tipo": str,
            "obligatorio": True,
            "atributo": "url",
            "descripcion": "url a consultar",
            "ejemplo": "localhost",
        }

        propiedadAuth = {
            "nombre": "auth",
            "tipo": list,
            "obligatorio": False,
            "atributo": "auth",
            "descripcion": "usuario  a consultar",
            "ejemplo": "localhost",
        }

        propiedadJson = {
            "nombre": "JSON",
            "tipo": list,
            "obligatorio": False,
            "atributo": "json",
            "descripcion": "duración de la espera",
            "ejemplo": "1:32",
        }

        propiedadHeaders = {
            "nombre": "headers",
            "tipo": list,
            "obligatorio": False,
            "atributo": "headers",
            "descripcion": "agregar cabecera a consulta",
            "ejemplo": "1:32",
        }

        self.agregarPropiedad(propiedadURL)
        self.agregarPropiedad(propiedadAuth)
        self.agregarPropiedad(propiedadJson)
        self.agregarPropiedad(propiedadHeaders)

        self.funcion = self.esperarTiempo

    def esperarTiempo(self):
        """espera un tiempo"""
        tiempo = self.obtenerValor("tiempo")
        if tiempo is not None:
            # TODO: confirmar que es un numero
            if isinstance(tiempo, str):
                pedadosTiempo = tiempo.split(":")
                segundos = int(pedadosTiempo[-1])
                if len(pedadosTiempo) > 1:
                    segundos += int(pedadosTiempo[-2]) * 60
                if len(pedadosTiempo) > 2:
                    segundos += int(pedadosTiempo[-3]) * 3600
                tiempo = segundos

        Logger.info(f"Delay[{tiempo}s]")
        time.sleep(tiempo)
