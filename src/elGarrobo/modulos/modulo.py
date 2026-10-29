import json
import operator
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from elGarrobo.accionesOOP.accion import accion
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.accionesOOP.herramientas.valoresAccion import valoresAcciones

ARCHIVO_EVENTOS = "eventos"
"Archivo global (no por perfil) con las acciones que se disparan con los eventos de los módulos"

OPERADORES = {
    ">=": operator.ge,
    "<=": operator.le,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    "=": operator.eq,
}
"Condiciones del filtro (ej. '> 80'); los de dos caracteres primero para que '>=' no se lea como '>'"

filtrosCumplidos: set[str] = set()
"Entradas de eventos periódicos que cumplían el filtro en la lectura anterior"

FASES_IMPRESION = {
    "imprimiendo": ("impresion_iniciada", "Una impresora empezó a imprimir"),
    "terminada": ("impresion_terminada", "Una impresora terminó de imprimir"),
    "cancelada": ("impresion_cancelada", "Se canceló una impresión"),
    "error": ("impresion_error", "Una impresión falló"),
    "pausada": ("impresion_pausada", "Una impresora pausó la impresión"),
}
"Fase de una impresora (como la traduce cada módulo) → (evento, descripción); 'inactiva' no avisa"


@dataclass
class eventoModulo:
    """Evento que un módulo puede emitir; la GUI arma con él el desplegable, el filtro y la ayuda de variables"""

    nombre: str
    "Nombre en eventos.md, ej. fdm_monster/impresion_terminada"
    descripcion: str
    datos: dict[str, str] = field(default_factory=dict)
    "Dato → valor de ejemplo; se usan como {dato} en las opciones y Probar en la GUI manda los de ejemplo"
    periodico: bool = False
    "Llega en cada lectura (ej. RAM cada 10 s): las acciones se ejecutan solo cuando el filtro empieza a cumplirse"


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
    funcionEvento: Optional[Callable[[str, dict, bool], None]] = None
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
            periodico = any(evento.periodico for evento in self.eventos if evento.nombre == nombre)
            modulo.funcionEvento(nombre, datos, periodico)


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


def eventosImpresion(prefijo: str, datos: dict[str, str]) -> list[eventoModulo]:
    """Catálogo de eventos de impresión de un módulo (ej. klipper/impresion_terminada); el de error agrega {motivo}"""
    motivo = {"motivo": "Heater extruder not heating"}
    return [
        eventoModulo(f"{prefijo}/{evento}", descripcion, datos | (motivo if fase == "error" else {}))
        for fase, (evento, descripcion) in FASES_IMPRESION.items()
    ]


def eventoImpresion(anterior: Optional[str], actual: str) -> Optional[str]:
    """Evento al cambiar de fase; None en la primera lectura (no se sabe qué pasó antes), sin cambio o al reanudar"""
    if anterior is None or anterior == actual or (anterior == "pausada" and actual == "imprimiendo"):
        return None
    return FASES_IMPRESION.get(actual, (None, None))[0]


def cumpleFiltro(esperado: Any, valor: Any) -> bool:
    """Si el dato cumple lo del filtro: '> 80', '>= 80', '< 20', '<= 20', '!= 0', '= x' o el valor solo (igualdad)

    Se compara como número (90 = 90.0); si alguno no es número, solo = y != comparan como texto
    """
    texto = str(esperado).strip()
    simbolo = next((simbolo for simbolo in OPERADORES if texto.startswith(simbolo)), "=")
    objetivo = texto.removeprefix(simbolo).strip()
    comparar = OPERADORES[simbolo]
    try:
        return comparar(float(valor), float(objetivo))
    except (TypeError, ValueError):
        return simbolo in ("=", "!=") and comparar(str(valor), objetivo)


def accionesEvento(entradas: list, nombre: str, datos: dict[str, Any], periodico: bool = False) -> list[dict]:
    """Entradas de eventos.md activas del evento cuyo filtro se cumple, con los {dato} reemplazados

    Si el evento es periódico solo las que empiezan a cumplirlo: ram > 80 avisa al pasar de 80, no en cada lectura
    """
    acciones = []
    for entrada in entradas:
        if not isinstance(entrada, dict) or entrada.get("evento") != nombre:
            continue
        filtro = entrada.get("filtro") or {}
        cumple = entrada.get("activo") is not False and all(cumpleFiltro(v, datos.get(k)) for k, v in filtro.items())
        if periodico:
            # ponytail: una sola fuente por evento periódico (un PC); con varias, la clave también llevaría la fuente
            clave = json.dumps(entrada, sort_keys=True, default=str)
            antes = clave in filtrosCumplidos
            if cumple:
                filtrosCumplidos.add(clave)
            else:
                filtrosCumplidos.discard(clave)
            cumple = cumple and not antes
        if cumple:
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
