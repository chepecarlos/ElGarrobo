import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from elGarrobo.accionesOOP.accion import accion
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.accionesOOP.herramientas.valoresAccion import valoresAcciones

ARCHIVO_EVENTOS = "eventos"
"Archivo global (no por perfil) con las acciones que se disparan con los eventos de los módulos"


@dataclass
class eventoModulo:
    """Evento que un módulo puede emitir; la GUI arma con él el desplegable, el filtro y la ayuda de variables"""

    nombre: str
    "Nombre en eventos.md, ej. fdm_monster/impresion_terminada"
    descripcion: str
    datos: dict[str, str] = field(default_factory=dict)
    "Dato → valor de ejemplo; se usan como {dato} en las opciones y Probar en la GUI manda los de ejemplo"


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
    eventos: list[eventoModulo] = []
    """Eventos que emite el módulo con `emitirEvento`"""
    valoresDatos: dict[str, list[str]] = {}
    """Dato → valores reales vistos al correr (ej. nombres de impresoras); la GUI los ofrece en el filtro.
    Se asigna en la clase hija (no se modifica este dict, es compartido)"""
    funcionEvento: Optional[Callable[[str, dict], None]] = None
    """Inyectada por elGarrobo: ejecuta las acciones de eventos.md del evento"""

    def __init__(self, dataModulo: dict) -> None:
        pass

    def obtenerValor(self, listaValores: list[valoresAcciones], atributo: str):
        """Devuelve el valores configurado"""
        for valor in listaValores:
            if atributo == valor.atributo:
                return valor.valor

    def ejecutar(self):
        pass

    def emitirEvento(self, nombre: str, datos: dict[str, str]) -> None:
        """Avisa un evento (ej. fdm_monster/impresion_terminada); el módulo no sabe qué acciones tiene asignadas"""
        # modulo y no self: los hijos usan el atributo `modulo` para su clave en modulos.md
        if modulo.funcionEvento is not None:
            modulo.funcionEvento(nombre, datos)


def reemplazarDatos(valor: Any, datos: dict[str, Any]) -> Any:
    """Copia de valor con {dato} cambiado por su valor en los textos, también en dicts y listas (ej. pasos de macro)

    Solo los datos del evento: otras llaves como el {print $1} de awk quedan igual
    """
    if isinstance(valor, str):
        if not datos:
            return valor
        patron = r"\{(" + "|".join(re.escape(dato) for dato in datos) + r")\}"
        return re.sub(patron, lambda encontrado: str(datos[encontrado.group(1)]), valor)
    if isinstance(valor, dict):
        return {clave: reemplazarDatos(v, datos) for clave, v in valor.items()}
    if isinstance(valor, list):
        return [reemplazarDatos(v, datos) for v in valor]
    return valor


def accionesEvento(entradas: list, nombre: str, datos: dict[str, Any]) -> list[dict]:
    """Entradas de eventos.md activas del evento cuyo filtro coincide, con los {dato} reemplazados"""
    acciones = []
    for entrada in entradas:
        if not isinstance(entrada, dict) or entrada.get("evento") != nombre or entrada.get("activo") is False:
            continue
        # ponytail: solo igualdad; condiciones (ej. progreso > 50) quedan en mejoras.md
        filtro = entrada.get("filtro") or {}
        if any(str(datos.get(clave)) != str(valor) for clave, valor in filtro.items()):
            continue
        acciones.append(reemplazarDatos(entrada, datos))
    return acciones


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


def leerMonitoreo(config: dict) -> tuple[int, int, int]:
    """Lee intervalo, intervalo con error y límite de errores con los defectos de `propiedadesMonitoreo()`

    Un valor inválido usa el defecto; el intervalo mínimo es 5, el de error no baja del intervalo y el límite mínimo es 1
    """
    defectos = {propiedad.atributo: propiedad.defecto for propiedad in propiedadesMonitoreo()}

    def leer(atributo: str) -> int:
        try:
            return int(config.get(atributo, defectos[atributo]))
        except (TypeError, ValueError):
            return defectos[atributo]

    intervalo = max(5, leer("intervalo_segundos"))
    return intervalo, max(intervalo, leer("intervalo_error_segundos")), max(1, leer("limite_errores_log"))
