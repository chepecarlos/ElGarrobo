"""Acción para esperar un tiempo"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accionBase import accionBase

Logger = ConfigurarLogging(__name__)


class accionPresionar(accionBase):
    "Ejecuta una accion si se preciona y otra cuando se suelta"

    nombre = "Presiona"
    comando = "presionar"
    descripcion = "Ejecuta una accion si se preciona y otra cuando se suelta"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadPresionado = {
            "nombre": "Precionado",
            "tipo": dict,  # TODO: que entienda que es una accion
            "obligatorio": True,
            "atributo": "presionado",
            "descripcion": "Acción para ejecutarse cuando se presione",
            "ejemplo": "---",
        }

        propiedadSoltar = {
            "nombre": "Soltar",
            "tipo": dict,  # TODO: que entienda que es una accion
            "obligatorio": True,
            "atributo": "soltar",
            "descripcion": "Acción para ejecutarse cuando se Suelte",
            "ejemplo": "---",
        }

        propiedadEstado = {
            "nombre": "Estado",
            "tipo": bool,
            "obligatorio": False,
            "atributo": "estado",
            "descripcion": "",
            "ejemplo": "---",
        }

        self.agregarPropiedad(propiedadPresionado)
        self.agregarPropiedad(propiedadSoltar)
        self.agregarPropiedad(propiedadEstado)
