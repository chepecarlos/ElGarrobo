import logging

from Extra.FuncionesLogging import ConfigurarLogging
from Extra.MiStreanDeck import CargarStrean
from Extra.FuncionesArchivos import ObtenerArchivo

import Extra.MiTecladoMacro as TecladoMacro
import Extra.MiStreanDeck as MiStreanDeck

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class ElGatito(object):

    def __init__(self, Data):
        self.Data = Data
        self.CargarData()
        self.CargarTeclados()
        self.CargarStreanDeck()

    def CargarData(self):
        """Cargando Data para Dispisitivo"""
        logger.info("Cargando Data")
        if 'Deck_file' in self.Data:
            self.Data['Deck'] = ObtenerArchivo(self.Data['Deck_file'])

        if 'Teclados_file' in self.Data:
            self.Data['Teclados'] = ObtenerArchivo(self.Data['Teclados_file'])

    def CargarTeclados(self):
        """Confiurando Teclados Macros"""
        if 'Teclados' in self.Data:
            logger.info("Cargando Teclados")
            self.ListaTeclados = []
            for Teclado in self.Data['Teclados']:
                TecladoActual = TecladoMacro.MiTecladoMacro(Teclado['Nombre'], Teclado['Input'], Teclado['File'])
                if TecladoActual.Conectar():
                    self.ListaTeclados.append(TecladoActual)
            # self.ConfigurandoTeclados("")

    def CargarStreanDeck(self):
        """configurando StreanDeck"""
        self.ListaDeck = []
        if 'Deck' in self.Data:
            logger.info("Cargando StreamDeck")
            CargarDeck = CargarStrean(self.Data['Deck'])
            for Deck in CargarDeck:
                DeckActual = MiStreanDeck.MiStreanDeck(Deck)
                self.ListaDeck.append(DeckActual)

    def ConfigurandoTeclados(self, Directorio):
        for Teclado in self.ListaTeclados:
            Teclado.ActualizarTeclas(Directorio)

    # def ConfigurandoSteanDeck(self, Direcotio):
    #     for Deck in slef.ListaDeck:
    #         print()
