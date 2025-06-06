import pyautogui

from elGarrobo.accionesOOP.accionBase import accionBase
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


class accionEscribirTexto(accionBase):
    """Escribe un texto como un teclado"""

    def __init__(self) -> None:
        nombre = "Escribir texto"
        comando = "escribir"
        descripcion = "Escribe un texto como un teclado"
        super().__init__(nombre, comando, descripcion)

        propiedadTexto = {
            "nombre": "Texto",
            "tipo": str,
            "obligatorio": True,
            "atributo": "texto",
            "descripcion": "texto a escribir",
            "ejemplo": "Hola mundo",
        }

        propiedadVelocidad = {
            "nombre": "Velocidad",
            "tipo": float,
            "obligatorio": False,
            "atributo": "intervalo",
            "descripcion": "Intervalo entre letra a letra cuando se escriba en segundos",
            "ejemplo": "0.01",
            "defecto": 0.01,
        }

        self.agregarPropiedad(propiedadTexto)
        self.agregarPropiedad(propiedadVelocidad)

        self.funcion = self.comandoEscribir

    def comandoEscribir(self):
        """Escribe un texto"""

        texto = self.obtenerValor("texto")
        intervalo = self.obtenerValor("intervalo")

        if texto is not None and intervalo is not None:
            pyautogui.write(texto, interval=intervalo)
            logger.info(f"Escribiendo[{texto}] v{intervalo}s")
        else:
            logger.error("Falta valores para escribir")
