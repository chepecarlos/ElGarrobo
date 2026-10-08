"""Acción que ejecuta una acción al presionar la tecla y otra al soltarla"""

from elGarrobo.miLibrerias import ConfigurarLogging

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionPresionar(accion):
    "Ejecuta una acción al presionar la tecla y otra al soltarla"

    nombre = "Presiona"
    comando = "presionar"
    descripcion = "Ejecuta una acción al presionar la tecla y otra al soltarla"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadPresionado = propiedadAccion(
            nombre="Presionado",
            tipo=dict,  # TODO: que entienda que es una accion
            obligatorio=True,
            atributo="presionado",
            descripcion="Acción para ejecutarse cuando se presione",
            ejemplo="---",
        )

        propiedadSoltar = propiedadAccion(
            nombre="Soltar",
            tipo=dict,  # TODO: que entienda que es una accion
            obligatorio=True,
            atributo="soltar",
            descripcion="Acción para ejecutarse cuando se suelte",
            ejemplo="---",
        )

        propiedadEstado = propiedadAccion(
            nombre="Estado",
            tipo=bool,
            obligatorio=False,
            atributo="estado",
            descripcion="",
            ejemplo="---",
        )

        self.agregarPropiedad(propiedadPresionado)
        self.agregarPropiedad(propiedadSoltar)
        self.agregarPropiedad(propiedadEstado)
