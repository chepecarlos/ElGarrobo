from .accionBase import accionBase
import time

from elGarrobo.miLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


class accionDelay(accionBase):
    def __init__(self) -> None:
        nombre = "Delay"
        comando = "delay"
        descripcion = "Espera una cantidad de tiempo"
        super().__init__(nombre, comando, descripcion)

        propiedadTiempo = {
            "nombre": "Tiempo",
            "tipo": str,
            "obligatorio": True,
            "atributo": "tiempo",
            "descripcion": "duración de la espera",
            "ejemplo": "1:32",
        }

        self.agregarPropiedad(propiedadTiempo)

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
