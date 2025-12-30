from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionVolumen(accion):
    """Siguiente pagina en Dispositivo StreamDeck"""

    nombre = "Volumen"
    comando = "volumen"
    descripcion = "Cambia Volumen dispositivo virtual de pulse"

    propiedadDispositivo: propiedadAccion = propiedadAccion(
        nombre="Dispositivo",
        tipo=str,
        obligatorio=True,
        atributo="dispositivo",
        descripcion="Nombre del dispositivo a cambiar volumen",
        ejemplo="microfono",
    )

    propiedadValor: propiedadAccion = propiedadAccion(
        nombre="Valor",
        tipo=int,
        obligatorio=True,
        atributo="valor",
        descripcion="Incremento o decremento de volumen",
        ejemplo="+5",
    )

    propiedadOpciones: propiedadAccion = propiedadAccion(
        nombre="Opción",
        tipo=str,
        obligatorio=False,
        atributo="opcion",
        descripcion="asignar o incrementar",
        ejemplo="+5",
        defecto="asignar",
    )

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        self.agregarPropiedad(self.propiedadDispositivo)
        self.agregarPropiedad(self.propiedadValor)
        self.agregarPropiedad(self.propiedadOpciones)
