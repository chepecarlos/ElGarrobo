import os
from enum import Enum
from typing import Type

from elGarrobo.miLibrerias import (
    ConfigurarLogging,
    ObtenerArchivo,
    ObtenerFolderConfig,
    SalvarArchivo,
)

logger = ConfigurarLogging(__name__)


class dispositivoBase:
    "Clase base de dispositovos fisicos que ejecutan las acciones"

    estadoTecla = Enum("estadoTecla", [("PRESIONADA", 1), ("LIBERADA", 2), ("MANTENIDA", 3)])

    nombre: str
    "Nombre propio del dispositivo"
    dispositivo: str
    "Ruta virtual de donde se encuentra dispositivo"
    archivo: str
    "Archivos por folder donde se cargara la acciones"
    ejecutarAcción: callable
    "Función que se llama para ejecutar una acción"
    conectado: bool
    "El dispositivo esta listo para usarse"
    folder: str
    "Ruta de las acciones cargadas"
    folderPerfil: str
    "Carpeta del perfil actual"
    listaAcciones: list
    "Lista de Acciones cargadas"
    tipo: str = ""
    "Tipo de dispositivo"
    clase: str
    "Sub Categoria del dispositivo"
    actualizarPestaña: callable
    "función que actualiza la pestaña del dispositivo con nuevas acciones"
    modulo: str = ""
    "Modulo para cargar dispositivo"
    archivoConfiguracion: str = ""
    activado: bool = True
    "Si el dispositivo esta activo o no"
    ejecutarAcción: callable = None
    "Función que se llama para ejecutar una acción"

    def __init__(self, nombre: str = None, dispositivo: str = None, archivo: str = None, folderPerfil: str = None):
        """Inicializa un dispositivo base.

        Args:
            nombre (str): Nombre del dispositivo
            dispositivo (str): Ruta del dispositivo
            archivo (str): Ruta del archivo de configuración
            folderPerfil (str): Carpeta del perfil
        """
        if nombre is not None:
            self.nombre = nombre
        if dispositivo is not None:
            self.dispositivo = dispositivo
        if archivo is not None:
            self.archivo = archivo
        self._listaAcciones: list[dict] = list()
        self.folder = "/"
        if folderPerfil is not None:
            self.folderPerfil = folderPerfil
        self.ejecutarAcción = None
        # self.tipo = ""
        self.clase = ""
        self.actualizarPestaña = None
        self.pestaña = None
        self.panel = None

    @staticmethod
    def cargarDispositivos(modulosCargados: dict, claseDispositivo: type["dispositivoBase"]) -> list[Type["dispositivoBase"]]:
        """
        Preparara la informacion de los dispositivos en base a una clase

        Args:
            modulosCargados (dict): Dispositivos cargados y desactivados
            claseDispositivo (dispositivoBase): Clase del dispositivo a cargar es basada es dispositivoBase

        Returns:
            list (dispositivoBase): Lista de dispositivos configurados
        """

        listaDispositivos: list[Type[dispositivoBase]] = list()

        moduloCargado = modulosCargados.get(claseDispositivo.modulo)
        if moduloCargado is None or moduloCargado is False:
            logger.error(f"No cargado {claseDispositivo.tipo}")
            return listaDispositivos
        logger.info(f"{claseDispositivo.tipo}[Cargando]")

        dataDispositivos = ObtenerArchivo(claseDispositivo.archivoConfiguracion)

        for dataActual in dataDispositivos:
            dispositivoActual = claseDispositivo(dataActual)
            listaDispositivos.append(dispositivoActual)

        return listaDispositivos

    def conectar(self) -> bool:
        """Intenta conectar el dispositivo

        Returns:
            bool: False si fallo la conexión
        """
        pass

    def desconectar(self):
        "Desconecta el dispositivo"
        pass

    def actualizar(self):
        pass

    def cargarAccionesFolder(self, folder: str, directo: bool = False, recargar: bool = False):
        """Busca y carga acciones en un folder, si existen

        Args:
            folder (str):
            directo (bool, optional): . Defaults to False.
            recargar (boo, optional):

        """

        if not self.activado:
            return

        folderBase = str(ObtenerFolderConfig())
        rutaRelativa = self._calcularRutaRelativa(folder)

        if self.folder == rutaRelativa or self.folder is None and not recargar:
            if directo:
                logger.info(f"{self.nombre}[Acciones-Cargadas] - {self.folder} - Ya cargado")
            return

        archivo = os.path.abspath(os.path.join(folderBase, self.folderPerfil, rutaRelativa, self.archivo))
        data = self.cargarData(archivo)

        if data is not None:
            self.listaAcciones = data
            if rutaRelativa in (".", "..", ""):
                self.folder = "/"
            else:
                self.folder = rutaRelativa
            logger.info(f"{self.nombre}[Acciones-Cargadas] - {self.folder} - Acciones:[{len(self.listaAcciones)}]")
        elif directo:
            logger.warning(f"{self.nombre}[{self.tipo}] - No se puede cargar {archivo}")

    def _calcularRutaRelativa(self, folder: str) -> str:
        "Calcula la ruta relativa basada en el folder actual y el nuevo folder"
        if folder.startswith("/"):
            return folder.lstrip("/")
        elif self.folder == "/" and folder in ("../", ".", ".."):
            return ""
        else:
            return os.path.normpath(os.path.join(self.folder.lstrip("/"), folder))

    def cargarAccionesRegresarFolder(self, directo: bool = False):
        print(f"Intentando subir folder {self.nombre}- {self.folder}")
        self.cargarAccionesFolder("../", directo)

    def recargarAccionesFolder(self, directo: bool = False):
        "Recarga las acciones del folder actual"
        self.cargarAccionesFolder(".", directo, recargar=True)

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
        if self.actualizarPestaña is not None:
            self.actualizarPestaña(self)

    def salvarAcciones(self):
        folderBase = str(ObtenerFolderConfig())
        archivo = os.path.abspath(os.path.join(folderBase, self.folderPerfil, self.folder.lstrip("/"), self.archivo))
        accionesSalvar = self.listaAcciones.copy()

        for acción in accionesSalvar:
            if isinstance(acción, dict):
                for propiedad, valor in acción.items():
                    if "__" in propiedad:
                        del acción[propiedad]

        SalvarArchivo(f"{archivo}.md", accionesSalvar)

    def asignarPerfil(self, folderPerfil: str):
        self.folderPerfil = folderPerfil
        self.folder = "/"
        # TODO: Cargar las acciones si es necesario
        # self.listaAcciones = list()
        # self.cargarAccionesFolder(".", directo=True, recargar=True)

    def buscarAccion(self, tecla: str, estado: estadoTecla):
        for acción in self.listaAcciones:
            if acción.get("key") == tecla:
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

    def __str__(self):
        return f"{self.nombre}[{self.tipo}]"
