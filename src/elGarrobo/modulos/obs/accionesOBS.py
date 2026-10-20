"""Acciones para controlar OBS"""

from typing import TYPE_CHECKING

from elGarrobo.accionesOOP.accion import accion, propiedadAccion
from elGarrobo.miLibrerias import ConfigurarLogging

if TYPE_CHECKING:
    from .moduloOBS import moduloOBS

logger = ConfigurarLogging(__name__)


def propiedadTexto(nombre: str, atributo: str, descripcion: str, ejemplo: str, obligatorio: bool = True):
    """Propiedad de texto, la mayoría de las acciones de OBS usan nombres de escena, fuente o filtro"""
    return propiedadAccion(
        nombre=nombre, atributo=atributo, tipo=[str], obligatorio=obligatorio, descripcion=descripcion, ejemplo=ejemplo
    )


class accionOBS(accion):
    """Base de las acciones de OBS, solo se ejecutan si OBS está conectado"""

    modulo: "moduloOBS" = None
    "Instancia del módulo OBS, se asigna al registrar la acción"
    requiereConexion: bool = True
    "Si es False se ejecuta aunque OBS no esté conectado"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

    def sePuedeEjecutar(self) -> bool:
        if self.modulo is None:
            logger.error(f"OBS[Módulo no cargado] {self.comando}")
            return False
        if self.requiereConexion and not self.modulo.conectado:
            logger.warning("OBS[No conectado]")
            self.modulo.Notificar("OBS-No-Conectado")
            return False
        return super().sePuedeEjecutar()


class accionOBSConectar(accionOBS):
    """Se conecta a OBS WebSocket"""

    nombre = "Conectar OBS"
    comando = "obs_conectar"
    descripcion = "Se conecta a OBS WebSocket"
    requiereConexion = False

    def __init__(self) -> None:
        super().__init__()
        self.agregarPropiedad(
            propiedadTexto("Servidor", "servidor", "Dirección de OBS", "localhost", obligatorio=False)
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Puerto",
                atributo="puerto",
                tipo=[int, str],
                descripcion="Puerto de OBS WebSocket",
                ejemplo="4455",
                defecto=4455,
            )
        )
        self.agregarPropiedad(
            propiedadTexto("Contraseña", "password", "Contraseña de OBS WebSocket", "clave", obligatorio=False)
        )
        self.funcion = lambda: self.modulo.conectar(
            self.obtenerValor("servidor", "localhost"), self.obtenerValor("puerto"), self.obtenerValor("password")
        )


class accionOBSDesconectar(accionOBS):
    """Se desconecta de OBS WebSocket"""

    nombre = "Desconectar OBS"
    comando = "obs_desconectar"
    descripcion = "Se desconecta de OBS WebSocket"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = lambda: self.modulo.desconectar()


class accionOBSGrabar(accionOBS):
    """Empieza o detiene la grabación"""

    nombre = "Grabar OBS"
    comando = "obs_grabar"
    descripcion = "Empieza o detiene la grabación de OBS"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = lambda: self.modulo.cambiarGrabacion()


class accionOBSPausar(accionOBS):
    """Pausa o continúa la grabación"""

    nombre = "Pausar OBS"
    comando = "obs_pausar"
    descripcion = "Pausa o continúa la grabación de OBS"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = lambda: self.modulo.cambiarPausa()


class accionOBSEnVivo(accionOBS):
    """Empieza o detiene la transmisión"""

    nombre = "En Vivo OBS"
    comando = "obs_envivo"
    descripcion = "Empieza o detiene la transmisión de OBS"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = lambda: self.modulo.cambiarEnVivo()


class accionOBSCamaraVirtual(accionOBS):
    """Activa o desactiva la cámara virtual"""

    nombre = "Cámara Virtual OBS"
    comando = "obs_camara_virtual"
    descripcion = "Activa o desactiva la cámara virtual de OBS"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = lambda: self.modulo.cambiarCamaraVirtual()


class accionOBSEscena(accionOBS):
    """Cambia la escena de programa"""

    nombre = "Escena OBS"
    comando = "obs_escena"
    descripcion = "Cambia la escena de programa de OBS"

    def __init__(self) -> None:
        super().__init__()
        self.agregarPropiedad(propiedadTexto("Escena", "escena", "Nombre de la escena", "Camara"))
        self.funcion = lambda: self.modulo.cambiarEscena(self.obtenerValor("escena"))


class accionOBSFuente(accionOBS):
    """Muestra u oculta una fuente de la escena actual de OBS"""

    nombre = "Fuente OBS"
    comando = "obs_fuente"
    descripcion = "Muestra u oculta una fuente de la escena actual de OBS"

    def __init__(self) -> None:
        super().__init__()
        self.agregarPropiedad(propiedadTexto("Fuente", "fuente", "Nombre de la fuente en la escena actual", "Camara"))
        self.funcion = lambda: self.modulo.cambiarFuente(self.obtenerValor("fuente"))


class accionOBSFiltro(accionOBS):
    """Activa o desactiva un filtro de una fuente"""

    nombre = "Filtro OBS"
    comando = "obs_filtro"
    descripcion = "Activa o desactiva un filtro de una fuente, sin estado lo invierte"

    def __init__(self) -> None:
        super().__init__()
        self.agregarPropiedad(propiedadTexto("Fuente", "fuente", "Fuente que tiene el filtro", "Camara"))
        self.agregarPropiedad(propiedadTexto("Filtro", "filtro", "Nombre del filtro", "Color"))
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Estado",
                atributo="estado",
                tipo=[bool],
                descripcion="True activa, False desactiva, sin valor invierte",
                ejemplo="true",
            )
        )
        self.funcion = lambda: self.modulo.cambiarFiltro(
            self.obtenerValor("fuente"), self.obtenerValor("filtro"), self.obtenerValor("estado")
        )


class accionOBSFiltroPropiedad(accionOBS):
    """Cambia una propiedad de un filtro"""

    nombre = "Propiedad Filtro OBS"
    comando = "obs_filtro_propiedad"
    descripcion = "Cambia una propiedad de un filtro, con agregar suma al valor anterior"

    def __init__(self) -> None:
        super().__init__()
        self.agregarPropiedad(propiedadTexto("Fuente", "fuente", "Fuente que tiene el filtro", "Camara"))
        self.agregarPropiedad(propiedadTexto("Filtro", "filtro", "Nombre del filtro", "Verde"))
        self.agregarPropiedad(propiedadTexto("Propiedad", "propiedad", "Propiedad del filtro", "similarity"))
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Valor",
                atributo="valor",
                tipo=[int, float, bool, str],
                obligatorio=True,
                descripcion="Nuevo valor de la propiedad",
                ejemplo="10",
            )
        )
        self.agregarPropiedad(
            propiedadAccion(
                nombre="Agregar",
                atributo="agregar",
                tipo=[bool],
                descripcion="Suma el valor al anterior en vez de reemplazarlo",
                ejemplo="true",
                defecto=False,
            )
        )
        self.funcion = lambda: self.modulo.cambiarFiltroPropiedad(
            self.obtenerValor("fuente"),
            self.obtenerValor("filtro"),
            self.obtenerValor("propiedad"),
            self.obtenerValor("valor"),
            self.obtenerValor("agregar"),
        )


class accionOBSGrabarVertical(accionOBS):
    """Empieza o detiene la grabación vertical"""

    nombre = "Grabar Vertical OBS"
    comando = "obs_grabar_vertical"
    descripcion = "Empieza o detiene la grabación del canvas de Aitum Vertical"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = lambda: self.modulo.cambiarGrabacionVertical()


class accionOBSEnVivoVertical(accionOBS):
    """Empieza o detiene la transmisión vertical"""

    nombre = "En Vivo Vertical OBS"
    comando = "obs_envivo_vertical"
    descripcion = "Empieza o detiene la transmisión del canvas de Aitum Vertical"

    def __init__(self) -> None:
        super().__init__()
        self.funcion = lambda: self.modulo.cambiarEnVivoVertical()


class accionOBSEscenaVertical(accionOBS):
    """Cambia la escena del canvas vertical"""

    nombre = "Escena Vertical OBS"
    comando = "obs_escena_vertical"
    descripcion = "Cambia la escena del canvas de Aitum Vertical"

    def __init__(self) -> None:
        super().__init__()
        self.agregarPropiedad(propiedadTexto("Escena", "escena", "Nombre de la escena vertical", "Camara_V"))
        self.funcion = lambda: self.modulo.cambiarEscenaVertical(self.obtenerValor("escena"))


class accionOBSFuenteVertical(accionOBS):
    """Muestra u oculta una fuente del canvas de Aitum Vertical"""

    nombre = "Fuente Vertical OBS"
    comando = "obs_fuente_vertical"
    descripcion = "Muestra u oculta una fuente del canvas de Aitum Vertical"

    def __init__(self) -> None:
        super().__init__()
        self.agregarPropiedad(
            propiedadTexto("Fuente", "fuente", "Nombre de la fuente en la escena vertical", "Camara")
        )
        self.agregarPropiedad(
            propiedadTexto(
                "Escena", "escena", "Escena vertical, si no se indica usa la actual", "Camara_V", obligatorio=False
            )
        )
        self.funcion = lambda: self.modulo.cambiarFuenteVertical(
            self.obtenerValor("fuente"), self.obtenerValor("escena")
        )


accionesOBS: list[type[accionOBS]] = [
    accionOBSConectar,
    accionOBSDesconectar,
    accionOBSGrabar,
    accionOBSPausar,
    accionOBSEnVivo,
    accionOBSCamaraVirtual,
    accionOBSEscena,
    accionOBSFuente,
    accionOBSFiltro,
    accionOBSFiltroPropiedad,
    accionOBSGrabarVertical,
    accionOBSEnVivoVertical,
    accionOBSEscenaVertical,
    accionOBSFuenteVertical,
]
"Acciones que registra el módulo OBS"
