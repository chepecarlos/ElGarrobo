import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Type

from elGarrobo.accionesOOP.accion import accion
from elGarrobo.dispositivos.dataAccion import dataAccion
from elGarrobo.dispositivos.dibujoBoton import dibujoBoton
from elGarrobo.miLibrerias import (
    ConfigurarLogging,
    ObtenerArchivo,
    ObtenerFolderConfig,
    SalvarArchivo,
)

logger = ConfigurarLogging(__name__)


@dataclass
class grupoBotones:
    """Botones físicos de un aparato, como los ve el usuario (ya rotado), en la página actual"""

    nombre: str
    filas: int
    columnas: int
    primeraTecla: int
    "Tecla del botón de arriba a la izquierda, siguen en orden de lectura"
    dibujante: "dispositivo"
    "Dispositivo que da tamaño, fuente y rotación para dibujar estos botones"


class dispositivo:
    "Clase base de dispositivos físicos que ejecutan las acciones"

    estadoTecla = Enum("estadoTecla", [("PRESIONADA", 1), ("LIBERADA", 2), ("MANTENIDA", 3)])

    nombre: str
    "Nombre propio del dispositivo"
    dispositivo: str = None
    "Ruta virtual de donde se encuentra dispositivo"
    archivo: str
    "Archivos por folder donde se cargara la acciones"
    ejecutarAcción: Callable[[dict, bool, int], Any] | None = None
    "Función que se llama para ejecutar una acción"
    conectado: bool = False
    "El dispositivo esta listo para usarse"
    folderActual: str | None = None
    "Folder donde esta leyendo las acciones cargadas"
    folderPerfil: str = "default"
    "Carpeta del perfil actual"
    listaAcciones: list | None = None
    "Lista de Acciones cargadas"
    _listaAcciones: list | None = None
    tipo: str = ""
    "Tipo de dispositivo"
    clase: str
    "Sub Categoria del dispositivo"
    funcionActualizarPestaña: Optional[Callable] = None
    "Función que llama actualizar la information de GUI"
    propiedadFolder: dict = dict()
    "propiedades para aplicar a todos los botos"

    pestaña = None
    "Pestaña del dispositivo en la interfaz"
    panel = None
    "Panel del dispositivo en la interfaz"
    nivelOrdenar: int = 0
    "Nivel para ordenar los dispositivos en la interfaz"

    modulo: str = ""
    "Modulo para cargar dispositivo"
    descripcion: str = ""
    "Descripción del tipo de dispositivo"
    archivoConfiguracion: str = ""
    activado: bool = True
    "Si el dispositivo esta activo o no"
    recargar: bool = True
    "Es necesario actualizar la imagen o titulo"

    listaIndexUsados: list = list()

    def __init__(self, dataConfiguración: dict = None) -> None:
        """Inicializa un dispositivo base.

        Args:
            dataConfiguración (dict): Datos de configuración del dispositivo
        """

        self.nombre = dataConfiguración.get("nombre")
        self.dispositivo = dataConfiguración.get("dispositivo", "")
        self.archivo = dataConfiguración.get("archivo", "")
        self.activado = dataConfiguración.get("activado", True)
        self.nivelOrdenar = dataConfiguración.get("ordenar", 0)

        self._listaAcciones: list[dict] = list()
        self.ejecutarAcción = None
        self.clase = ""
        self.funcionActualizarPestaña = None
        self.pestaña = None
        self.panel = None

    @staticmethod
    def cargarDispositivos(dispositivosCargados: dict, claseDispositivo: type["dispositivo"]) -> list["dispositivo"]:
        """
        Preparara la informacion de los dispositivos en base a una clase

        Args:
            dispositivosCargados (dict): Estado activado/desactivado de cada tipo de dispositivo (dispositivos.md)
            claseDispositivo (dispositivo): Clase del dispositivo a cargar es basada es dispositivo

        Returns:
            list (dispositivo): Lista de dispositivos configurados
        """

        listaDispositivos: list[dispositivo] = list()

        moduloCargado = dispositivosCargados.get(claseDispositivo.modulo)
        if moduloCargado is None or moduloCargado is False:
            logger.debug(f"No cargado Dispositivo-{claseDispositivo.tipo}")
            return listaDispositivos
        logger.info(f"Dispositivo-{claseDispositivo.tipo}[Cargando]")

        dataDispositivos = ObtenerArchivo(claseDispositivo.archivoConfiguracion)

        if dataDispositivos is None:
            logger.warning(
                f"Falta información para cargar {claseDispositivo.tipo} ",
                f"{claseDispositivo.archivoConfiguracion}",
            )
            return listaDispositivos

        for dataActual in dataDispositivos:
            dispositivoActual: dispositivo = claseDispositivo(dataActual)
            if dispositivoActual.activado:
                listaDispositivos.append(dispositivoActual)

        return listaDispositivos

    def conectar(self) -> bool:
        """Intenta conectar el dispositivo

        Returns:
            bool: False si fallo la conexión
        """
        logger.error(f"Falta implementar conectar en {self.tipo}")

        raise (NotImplementedError)

    def desconectar(self):
        "Desconecta el dispositivo"
        logger.error(f"Falta implementar desconectar en {self.tipo}")

    def cargarAccionesFolder(self, folderCargar: str = "/", recargar: bool = False):
        """Busca y carga acciones en un folder, si existen

        Args:
            folder (str): folder a cargar las acciones
            recargar (boo, optional): Es necesario recargar para leer nuevas acciones desde archivo

        """

        folderPerfil = self._folderConfigPerfil()

        folderBuscar = Path(folderCargar)

        if folderBuscar.is_absolute():
            folderBuscar = Path(folderCargar.lstrip("/"))
        else:
            folderBuscar = self.folderActual / folderBuscar

        folderData = (folderPerfil / folderBuscar).resolve()

        archivoData = (folderData / self.archivo).resolve()

        if folderPerfil not in archivoData.parents:
            logger.warning(f"{self.nombre}[{self.tipo}] - No se puede cargar acciones fuera de folder perfil")
            return

        if self.folderActual == folderData.relative_to(folderPerfil) and not recargar:
            return

        dataAcciones = self.cargarData(str(archivoData))

        if dataAcciones is None:
            logger.debug(f"{self.nombre}[{self.tipo}] - No se puede cargar acciones {folderBuscar}")
            return

        dataAcciones = self.convertirAcciones(dataAcciones)

        if self.listaAcciones == dataAcciones:
            logger.info(f"Data ya cargada {self.nombre} - {folderBuscar}")
            return

        self.recargar = True
        # Sin el setter: la GUI se avisa en accionesCargadas(), cuando folder y todo lo demás ya cambió
        self._listaAcciones = dataAcciones
        self.folderActual = folderData.relative_to(folderPerfil)
        logger.info(f"AccionesCargadas[{self.nombre}] {len(self.listaAcciones)} - /{self.folderActual}")
        self.accionesCargadas()
        return

    def accionesCargadas(self) -> None:
        """Se llama al cargar las acciones de un folder; los dispositivos agregan lo suyo antes de avisar a la GUI"""
        self.avisarGui()

    def avisarGui(self) -> None:
        """Redibuja la pestaña del dispositivo en la GUI, si hay: cambió de folder, de página, etc."""
        if self.funcionActualizarPestaña is not None:
            self.funcionActualizarPestaña(self)

    def dibujo(self) -> dibujoBoton:
        """Datos de este dispositivo y su folder para dibujar botones (vista previa en la GUI y StreamDeck)"""
        return dibujoBoton(
            folderPerfil=self._folderConfigPerfil(),
            folderActual=self.folderActual,
            archivoFuente=getattr(self, "archivoFuente", None),
            propiedadFolder=self.propiedadFolder,
            imagenesBase=getattr(self, "imagenesBase", None) or {},
            rotar=getattr(self, "rotar", 0),
        )

    def gruposBotones(self) -> list["grupoBotones"] | None:
        """Botones físicos de la página actual para dibujar el dispositivo en la GUI; None muestra la tabla"""
        return None

    def tamañoBoton(self) -> tuple[int, int]:
        """Tamaño en pixeles de los botones, 72x72 (StreamDeck Original) por defecto"""
        return (72, 72)

    def _folderConfigPerfil(self) -> Path:
        "Devuelve la ruta obsoleta del folder de perfil"

        folderConfig = Path(ObtenerFolderConfig())
        folderPerfil = Path(self.folderPerfil)
        return (folderConfig / folderPerfil).resolve()

    def regresarFolderActual(self, directo: bool = False):
        """Sube un folder a dispositivo y carga las acciones

        Ejemplo:
            home/pollo -> home
        """

        self.cargarAccionesFolder("../", directo)

    def recargarAccionesFolder(self):
        "Recarga las acciones del folder actual"
        self.cargarAccionesFolder(".", recargar=True)

    def cargarData(self, archivo: str) -> Any:
        """Carga datos desde un archivo.

        Args:
            archivo (str): Ruta del archivo a cargar.

        """

        tipoArchivos = [".md", ".json"]
        "Archivos a cargar información"

        if ".md" in archivo or ".json" in archivo:
            return ObtenerArchivo(archivo)

        for tipo in tipoArchivos:
            data = ObtenerArchivo(f"{archivo}{tipo}")
            if data is not None:
                return data

    def buscarAcción(self, data: dict):
        keyAcción: str = data.get("key")
        estado: bool = data.get("estado")

        for acción in self.listaAcciones:
            if str(acción.get("key")) == keyAcción:
                if self.ejecutarAcción is not None:
                    if estado:
                        print(f"Ejecutando acción: {acción}")
                        self.ejecutarAcción(acción)
                return
        if estado:
            print(f"No se encontró {keyAcción}-{self.nombre}")

    @property
    def listaAcciones(self):
        return self._listaAcciones

    @listaAcciones.setter
    def listaAcciones(self, data: list[dict | dataAccion]):
        self._listaAcciones = self.convertirAcciones(data)
        if self.funcionActualizarPestaña is not None:
            self.funcionActualizarPestaña(self)

    @staticmethod
    def convertirAcciones(data: list | None) -> list | None:
        """Convierte las entradas dict del .md/.json a dataAccion.

        Es en el mismo objeto lista porque el deck combinado la comparte con sus StreamDeck
        """
        if not isinstance(data, list):
            return data
        data[:] = [dataAccion.desdeDict(acción) if isinstance(acción, dict) else acción for acción in data]
        return data

    def salvarAcciones(self):
        folderBase = str(ObtenerFolderConfig())
        archivo = os.path.abspath(os.path.join(folderBase, self.folderPerfil, str(self.folderActual).lstrip("/"), self.archivo))
        # Las claves con "__" son estado en tiempo de ejecución, no se guardan
        accionesSalvar = [
            {propiedad: valor for propiedad, valor in acción.items() if "__" not in propiedad}
            if isinstance(acción, (dict, dataAccion))
            else acción
            for acción in self.listaAcciones
        ]

        SalvarArchivo(f"{archivo}.md", accionesSalvar)

        # Las acciones cambiaron (agregar, editar o borrar desde la GUI), redibujar el dispositivo
        self.recargar = True
        self.actualizar()

    def asignarPerfil(self, folderPerfil: str):
        self.folderPerfil = folderPerfil
        self.folderActual = "/"
        # TODO: Cargar las acciones si es necesario
        # self.listaAcciones = list()
        # self.cargarAccionesFolder(".", directo=True, recargar=True)

    def buscarAccion(self, tecla: str, estado: estadoTecla = estadoTecla.PRESIONADA, fuerza: int = 1) -> None:
        """Busca la accion a ejecutarse

        Args:
            tecla (str): cual tecla se precioso
            estado (estadoTecla): La tecla se precioso o se soltó
            fuerza (int, optional): Fuerza de la acción (por defecto es 1)
        """
        for acción in self.listaAcciones:
            if str(acción.get("key")) == str(tecla):
                if estado == self.estadoTecla.PRESIONADA:
                    if fuerza > 1:
                        logger.info(f"Evento[{acción.get('nombre')}] {self.nombre}[{tecla}-{estado.name}]x{fuerza}")
                    else:
                        logger.info(f"Evento[{acción.get('nombre')}] {self.nombre}[{tecla}-{estado.name}]")
                    self.ejecutarAcción(acción, True, fuerza)
                    return
                elif estado == self.estadoTecla.LIBERADA:
                    self.ejecutarAcción(acción, False, fuerza)
                    return
        if estado == self.estadoTecla.PRESIONADA:
            if fuerza > 1:
                logger.info(f"Evento[No asignado] {self.nombre}[{tecla}]x{fuerza}")
            else:
                logger.info(f"Evento[No asignado] {self.nombre}[{tecla}]")

    def configurarFuncionAccion(self, funcionAccion: Callable[[dict, bool, int], Any]) -> None:
        """Asigna la función que ejecuta acciones cuando el dispositivo recibe un evento.

        Todos los dispositivos (teclado, MQTT, GUI, etc.) llaman a esta función
        al detectar una interacción, pasando el dict de la acción para que el
        sistema central lo procese.

        Args:
            funcionAccion: Función con firma ``(accion: dict, estado: bool, fuerza: int) -> Any``.
                - accion:  dict con al menos ``"accion"`` y opcionalmente ``"opciones"``, ``"key"``, ``"nombre"``.
                - estado:  True si el evento es de presión/activación, False si es de liberación.
                - fuerza:  Multiplicador de intensidad (por defecto 1).
        """
        self.ejecutarAcción = funcionAccion

    @staticmethod
    def agregarIndexUsado(indexUsado: int):
        dispositivo.listaIndexUsados.append(indexUsado)

    def actualizar(self) -> None:
        """Actualiza la imagen del dispositivo"""
        self.recargar = False

    def __str__(self):
        return f"{self.nombre}[{self.tipo}]"

    def __repr__(self):
        return f"{self.nombre}[{self.tipo}]"
        return f"{self.nombre}[{self.tipo}]"
