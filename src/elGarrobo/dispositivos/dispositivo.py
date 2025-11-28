import os
from enum import Enum
from pathlib import Path
from typing import Type

from elGarrobo.miLibrerias import (
    ConfigurarLogging,
    ObtenerArchivo,
    ObtenerFolderConfig,
    SalvarArchivo,
)

logger = ConfigurarLogging(__name__)


class dispositivo:
    "Clase base de dispositivos físicos que ejecutan las acciones"

    estadoTecla = Enum("estadoTecla", [("PRESIONADA", 1), ("LIBERADA", 2), ("MANTENIDA", 3)])

    nombre: str
    "Nombre propio del dispositivo"
    dispositivo: str = None
    "Ruta virtual de donde se encuentra dispositivo"
    archivo: str
    "Archivos por folder donde se cargara la acciones"
    ejecutarAcción: callable
    "Función que se llama para ejecutar una acción"
    conectado: bool = False
    "El dispositivo esta listo para usarse"
    folderActual: str = None
    "Folder donde esta leyendo las acciones cargadas"
    folderPerfil: str = "default"
    "Carpeta del perfil actual"
    listaAcciones: list = None
    "Lista de Acciones cargadas"
    _listaAcciones: list = None
    tipo: str = ""
    "Tipo de dispositivo"
    clase: str
    "Sub Categoria del dispositivo"
    funcionActualizarPestaña: callable = None
    "Función que llama actualizar la information de GUI"

    pestaña = None
    "Pestaña del dispositivo en la interfaz"
    panel = None
    "Panel del dispositivo en la interfaz"

    modulo: str = ""
    "Modulo para cargar dispositivo"
    archivoConfiguracion: str = ""
    activado: bool = True
    "Si el dispositivo esta activo o no"
    ejecutarAcción: callable = None
    "Función que se llama para ejecutar una acción"
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

        self._listaAcciones: list[dict] = list()
        self.ejecutarAcción = None
        self.clase = ""
        self.funcionActualizarPestaña = None
        self.pestaña = None
        self.panel = None

    @staticmethod
    def cargarDispositivos(modulosCargados: dict, claseDispositivo: type["dispositivo"]) -> list[Type["dispositivo"]]:
        """
        Preparara la informacion de los dispositivos en base a una clase

        Args:
            modulosCargados (dict): Dispositivos cargados y desactivados
            claseDispositivo (dispositivo): Clase del dispositivo a cargar es basada es dispositivo

        Returns:
            list (dispositivo): Lista de dispositivos configurados
        """

        listaDispositivos: list[Type[dispositivo]] = list()

        moduloCargado = modulosCargados.get(claseDispositivo.modulo)
        if moduloCargado is None or moduloCargado is False:
            logger.debug(f"No cargado Dispositivo-{claseDispositivo.tipo}")
            return listaDispositivos
        logger.info(f"Dispositivo-{claseDispositivo.tipo}[Cargando]")

        dataDispositivos = ObtenerArchivo(claseDispositivo.archivoConfiguracion)

        if dataDispositivos is None:
            logger.warning(f"Falta información para cargar {claseDispositivo.tipo} {claseDispositivo.archivoConfiguracion}")
            return

        for dataActual in dataDispositivos:
            dispositivoActual = claseDispositivo(dataActual)
            if dispositivoActual.activado:
                listaDispositivos.append(dispositivoActual)

        return listaDispositivos

    def conectar(self) -> bool:
        """Intenta conectar el dispositivo

        Returns:
            bool: False si fallo la conexión
        """
        logger.error(f"Falta implementar conectar en {self.tipo}")

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

        if self.listaAcciones == dataAcciones:
            logger.info(f"Data ya cargada {self.nombre} - {folderBuscar}")
            return

        self.recargar = True
        self.listaAcciones = dataAcciones
        self.folderActual = folderData.relative_to(folderPerfil)
        logger.info(f"AccionesCargadas[{self.nombre}] {len(self.listaAcciones)} - /{self.folderActual}")
        return

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

    def cargarData(self, archivo: str) -> any:
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
    def listaAcciones(self, data: list[dict]):
        self._listaAcciones = data
        if self.funcionActualizarPestaña is not None:
            self.funcionActualizarPestaña(self)

    def salvarAcciones(self):
        folderBase = str(ObtenerFolderConfig())
        archivo = os.path.abspath(os.path.join(folderBase, self.folderPerfil, self.folderActual.lstrip("/"), self.archivo))
        accionesSalvar = self.listaAcciones.copy()

        for acción in accionesSalvar:
            if isinstance(acción, dict):
                for propiedad, valor in acción.items():
                    if "__" in propiedad:
                        del acción[propiedad]

        SalvarArchivo(f"{archivo}.md", accionesSalvar)

    def asignarPerfil(self, folderPerfil: str):
        self.folderPerfil = folderPerfil
        self.folderActual = "/"
        # TODO: Cargar las acciones si es necesario
        # self.listaAcciones = list()
        # self.cargarAccionesFolder(".", directo=True, recargar=True)

    def buscarAccion(self, tecla: str, estado: estadoTecla):
        for acción in self.listaAcciones:
            if str(acción.get("key")) == str(tecla):
                if estado == self.estadoTecla.PRESIONADA:
                    logger.info(f"Evento[{acción.get('nombre')}] {self.nombre}[{tecla}-{estado.name}]")
                    self.ejecutarAcción(acción, True)
                    return
                elif estado == self.estadoTecla.LIBERADA:
                    self.ejecutarAcción(acción, False)
                    return
        if estado == self.estadoTecla.PRESIONADA:
            logger.info(f"Evento[No asignado] {self.nombre}[{tecla}]")
        return None

    def configurarFuncionAccion(self, funcionAccion: callable):
        self.ejecutarAcción = funcionAccion

    @staticmethod
    def agregarIndexUsado(indexUsado: int):
        dispositivo.listaIndexUsados.append(indexUsado)
        pass

    def actualizar(self):
        "Actualiza la imagen del dispositivo"
        self.recargar = False

    def __str__(self):
        return f"{self.nombre}[{self.tipo}]"
