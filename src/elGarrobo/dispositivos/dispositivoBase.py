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
        self.folder = None
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
        print(folder[0])
        if folder[0] == "/":
            folder = folder[1:]
        else:
            # TODO; ver como entrar en subfolder
            pass
        print(folderBase, folderPerfil, folder, self.archivo)
        if self.folder == folder and self.folder is None:
            return

        archivo = os.path.join(folderBase, folderPerfil, folder, self.archivo)
        print(archivo)
        data = self.cargarData(archivo)

        if data is not None:
            self.listaAcciones = data
            print("Data salvada", self.listaAcciones)
        elif directo:
            logger.warning(f"{self.nombre}[{self.tipo}] - No se puede cargar {archivo}")

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
