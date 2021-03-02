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
        self.CargarData()
        self.CargarTeclados()
        self.CargarStreanDeck()
        CargarHilo()

    def CargarData(self):
        """Cargando Data para Dispisitivo"""
        logger.info("Cargando Data")
        if 'deck_file' in self.Data:
            self.Data['deck'] = ObtenerArchivo(self.Data['deck_file'])

        if 'teclados_file' in self.Data:
            self.Data['teclados'] = ObtenerArchivo(self.Data['teclados_file'])

        if 'folder_path' in self.Data:
            self.CargarFolder(self.Data)

        SalvarArchivo("Data.json", self.Data)

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
                        "folder_path": pathActual,
                        "folder": True}
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
                TecladoActual = MiTecladoMacro(Teclado['nombre'], Teclado['input'], Teclado['file'])
                if TecladoActual.Conectar():
                    self.ListaTeclados.append(TecladoActual)
            # self.ConfigurandoTeclados("")

    def CargarStreanDeck(self):
        """configurando StreanDeck"""
        self.ListaDeck = []
        if 'deck' in self.Data:
            if 'Dispositivos' in self.Data['deck']:
                logger.info("Cargando StreamDeck")
                CargarDeck = IniciarStreanDeck(self.Data['deck'])
                for Deck in CargarDeck:
                    DeckActual = MiStreanDeck(Deck)
                    self.ListaDeck.append(DeckActual)

    def ConfigurandoTeclados(self, Directorio):
        for Teclado in self.ListaTeclados:
            Teclado.ActualizarTeclas(Directorio)

    # def ConfigurandoSteanDeck(self, Direcotio):
    #     for Deck in slef.ListaDeck:
    #         print()
