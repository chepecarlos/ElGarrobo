import logging

from libreria.MiStreanDeck import IniciarStreanDeck, MiStreanDeck
from libreria.MiTecladoMacro import MiTecladoMacro
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import ObtenerArchivo, ObtenerFolder
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
            self.Data['folder'] = []
            ListaFolder = ObtenerFolder(self.Data['folder_path'])
            for Folder in ListaFolder:
                self.Data['folder'].append({"nombre": Folder, "folder": True})
            # for Folder in self.Data['folder']:
                # ListaFolder = ObtenerFolder([Folder['nombre']])
                # print(ListaFolder)
            #     # Folder['folder'] = ObtenerFolder(self.Data['folder_path'] + "/" + )
            #     logger.info(Folder['nombre'])
            logger.info(f"Folder cargados {self.Data['folder']}")

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
