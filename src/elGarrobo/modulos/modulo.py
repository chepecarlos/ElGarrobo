from elGarrobo.accionesOOP.accion import accion
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.accionesOOP.herramientas.valoresAccion import valoresAcciones


class modulo:

    nombre: str
    """Nombre del módulo"""
    modulo: str
    """Identificador del módulo"""
    descripcion: str
    """Descripción del módulo"""
    archivoConfiguracion: str = ""
    """Archivo de configuración del módulo"""
    activado: bool = True
    """Indica si el módulo está activado"""
    acciones: list[type[accion]] = []
    """Clases de acciones que se registran solo si el módulo está activado"""
    propiedades: list[propiedadAccion] = []
    """Opciones del archivo de configuración, la GUI arma el formulario con ellas"""

    def __init__(self, dataModulo: dict) -> None:
        pass

    def obtenerValor(self, listaValores: list[valoresAcciones], atributo: str):
        """Devuelve el valores configurado"""
        for valor in listaValores:
            if atributo == valor.atributo:
                return valor.valor

    def ejecutar(self):
        pass


def propiedadesMonitoreo() -> list[propiedadAccion]:
    """Opciones de los módulos que consultan un servicio cada cierto tiempo"""
    return [
        propiedadAccion(
            nombre="Intervalo",
            atributo="intervalo_segundos",
            tipo=[int],
            descripcion="Segundos entre consultas (mínimo 5)",
            defecto=30,
        ),
        propiedadAccion(
            nombre="Intervalo con error",
            atributo="intervalo_error_segundos",
            tipo=[int],
            descripcion="Segundos entre consultas cuando falla la conexión",
            defecto=120,
        ),
        propiedadAccion(
            nombre="Límite de errores en log",
            atributo="limite_errores_log",
            tipo=[int],
            descripcion="Errores seguidos que se registran antes de silenciarlos",
            defecto=3,
        ),
    ]
