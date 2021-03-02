import logging

from libreria.MiStreanDeck import IniciarStreanDeck, MiStreanDeck
from libreria.MiTecladoMacro import MiTecladoMacro
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import ObtenerArchivo, ObtenerFolder, UnirPath, SalvarArchivo, ObtenerArhivos
from libreria.FuncionesHilos import CargarHilo

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class ElGatito(object):

    def __init__(self, Data):
        self.Data = Data
        self.acciones = dict()
        self.CargarData()
        self.CargarTeclados()
        self.CargarStreanDeck()
        self.Prueba()
        CargarHilo()

    def CargarData(self):
        """Cargando Data para Dispisitivo"""
        logger.info("Cargando Data")
        if 'deck_file' in self.Data:
            self.Data['deck'] = ObtenerArchivo(self.Data['deck_file'])

        if 'teclados_file' in self.Data:
            self.Data['teclados'] = ObtenerArchivo(self.Data['teclados_file'])

        if 'folder_path' in self.Data:
            self.PathActual = self.Data['folder_path']
            self.Keys = {"nombre": self.Data['folder_path'],
                         "folder_path": self.Data['folder_path']}
            self.CargarFolder(self.Keys)

    def CargarFolder(self, Data):
        ListaFolder = ObtenerFolder(Data['folder_path'])
        ListaArchivos = ObtenerArhivos(Data['folder_path'])

        if len(ListaArchivos) > 0:
            for Archivo in ListaArchivos:
                self.CargarArchivos('teclados', Data, Archivo)
                self.CargarArchivos('global', Data, Archivo)
                self.CargarArchivos('deck', Data, Archivo)

        if len(ListaFolder) > 0:
            Data["folder"] = []
            for Folder in ListaFolder:
                pathActual = UnirPath(Data['folder_path'], Folder)
                data = {"nombre": Folder,
                        "folder_path": pathActual}
                Data["folder"].append(data)
            if "folder" in Data:
                for Folder in Data["folder"]:
                    self.CargarFolder(Folder)

    def CargarArchivos(self, Atributo, Data, Archivo):
        if Atributo in self.Data:
            for ArchivosTeclado in self.Data[Atributo]:
                if ArchivosTeclado['file'] == Archivo:
                    path = UnirPath(Data['folder_path'], Archivo)
                    DataArchivo = ObtenerArchivo(path)
                    DataAtributo = ArchivosTeclado['nombre']
                    Data[DataAtributo] = DataArchivo

    def CargarTeclados(self):
        """Confiurando Teclados Macros"""
        if 'teclados' in self.Data:
            logger.info("Cargando Teclados")
            self.ListaTeclados = []
            for Teclado in self.Data['teclados']:
                TecladoActual = MiTecladoMacro(Teclado['nombre'], Teclado['input'], Teclado['file'], self.Evento)
                if TecladoActual.Conectar():
                    self.ListaTeclados.append(TecladoActual)

    def CargarStreanDeck(self):
        """configurando StreanDeck"""
        self.ListaDeck = []
        if 'deck' in self.Data:
            logger.info("Cargando StreamDeck")
            CargarDeck = IniciarStreanDeck(self.Data['deck'], self.Evento)
            for Deck in CargarDeck:
                DeckActual = MiStreanDeck(Deck)
                self.ListaDeck.append(DeckActual)

    def ConfigurandoTeclados(self, Directorio):
        for Teclado in self.ListaTeclados:
            Teclado.ActualizarTeclas(Directorio)

    def BuscarFolder(self, Folder):
        Data = self.Keys
        Folderes = Folder.split('/')
        if len(Folderes) > 0:
            Data = self.BuscarDentroFolder(Folderes, Data)
            if Data is not None:
                SalvarArchivo("Data.json", Data)
                self.CargarAcciones('teclados', Data)
                self.CargarAcciones('global', Data)
                self.CargarAcciones('deck', Data)

    def CargarAcciones(self, Atributo, Data):
        for dispositivo in self.Data[Atributo]:
            nombreDispositivo = dispositivo['nombre']
            print(dispositivo)
            if nombreDispositivo in Data:
                logger.info(f"Encontro Config {Atributo} de {nombreDispositivo}")
                self.acciones[nombreDispositivo] = Data[nombreDispositivo]

    def BuscarDentroFolder(self, Folderes, Data):
        if 'nombre' in Data:
            if Data['nombre'] == Folderes[0]:
                Folderes.remove(Data['nombre'])
                if len(Folderes) > 0:
                    if 'folder' in Data:
                        for BuscarFolder in Data['folder']:
                            Data = self.BuscarDentroFolder(Folderes, BuscarFolder)
                            if Data is not None:
                                return Data
                else:
                    return Data

    def Evento(self, Evento):
        NombreEvento = Evento['nombre']
        if NombreEvento in self.acciones:
            for accion in self.acciones[NombreEvento]:
                if accion['key'] == Evento['key']:
                    logger.debug(f"Intentando hacer accion:{accion['key']}-{accion['nombre']}")
                    return
        logger.debug(Evento)

    def Prueba(self):
        self.PathActual = "defaul/news"
        self.BuscarFolder(self.PathActual)
        SalvarArchivo("acciones.json", self.acciones)
