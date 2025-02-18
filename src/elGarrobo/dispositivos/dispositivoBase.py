import os

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerArchivo, ObtenerFolderConfig

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
    listaAcciones: list
    "Lista de Acciones cargadas"
    tipo: str
    "Tipo de dispositivo"

    def __init__(self, nombre: str, dispositivo: str, archivo: str):
        self.nombre = nombre
        self.dispositivo = dispositivo
        self.archivo = archivo
        self.listaAcciones: list[dict] = list()
        self.folder = "/"
        self.ejecutarAcción = None
        self.tipo = ""

    def conectar(self):
        "Intenta conectar el dispositivo"
        pass

    def desconectar(self):
        "Desconecta el dispositivo"
        pass

    def actualizar(self):
        pass

    def cargarAccionesFolder(self, folderPerfil: str, folder: str, directo: bool = False):
        "Busca y carga acciones en un folder, si existen"
        folderBase = str(ObtenerFolderConfig())
        rutaRelativa = self._calcularRutaRelativa(folder)

        if self.folder == rutaRelativa or self.folder is None:
            if directo:
                logger.info(f"{self.nombre}[Acciones-Cargadas] - Ya cargado")
            return

        archivo = os.path.abspath(os.path.join(folderBase, folderPerfil, rutaRelativa, self.archivo))
        data = self.cargarData(archivo)

        if data is not None:
            self.listaAcciones = data
            if rutaRelativa in (".", "..", ""):
                self.folder = "/"
            else:
                self.folder = rutaRelativa
            logger.info(f"{self.nombre}[Acciones-Cargadas] - {self.folder}[{len(self.listaAcciones)}]")
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

    def cargarAccionesRegresarFolder(self, folderPerfil: str, directo: bool = False):
        print(f"Intentando subir folder {self.nombre}- {self.folder}")
        self.cargarAccionesFolder(folderPerfil, "../", directo)

    def cargarData(self, archivo: str):

        tipoArchivos = [".md", ".json"]

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
            if acción.get("key") == keyAcción:
                if self.ejecutarAcción is not None:
                    if estado:
                        print(f"Ejecutando acción: {acción}")
                        self.ejecutarAcción(acción)
                return
        if estado:
            print(f"No se encontró {keyAcción}-{self.nombre}")

    def __str__(self):
        print(f"{self.nombre}[{self.tipo}]")
