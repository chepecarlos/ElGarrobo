import os

from elGarrobo.miLibrerias import (
    ConfigurarLogging,
    ObtenerArchivo,
    ObtenerFolderConfig,
    SalvarArchivo,
)

logger = ConfigurarLogging(__name__)


class dispositivoBase:
    "Clase base de dispositovos fisicos que ejecutan las acciones"

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
    listaAcciones: list
    "Lista de Acciones cargadas"
    tipo: str
    "Tipo de dispositivo"
    clase: str
    "Sub Categoria del dispositivo"
    actualizarPestaña: callable
    "función que actualiza la pestaña del dispositivo con nuevas acciones"

    def __init__(self, nombre: str, dispositivo: str, archivo: str, folderPerfil: str):
        """Inicializa un dispositivo base.

        Args:
            nombre (str): Nombre del dispositivo
            dispositivo (str): Ruta del dispositivo
            archivo (str): Ruta del archivo de configuración
            folderPerfil (str): Carpeta del perfil
        """
        self.nombre = nombre
        self.dispositivo = dispositivo
        self.archivo = archivo
        self._listaAcciones: list[dict] = list()
        self.folder = "/"
        self.folderPerfil = folderPerfil
        self.ejecutarAcción = None
        self.tipo = ""
        self.clase = ""
        self.actualizarPestaña = None
        self.pestaña = None
        self.panel = None

    @staticmethod
    def cargarConfiguraciones():
        pass

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

    def __str__(self):
        return f"{self.nombre}[{self.tipo}]"
