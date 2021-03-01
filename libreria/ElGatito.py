import logging

from Extra.FuncionesLogging import ConfigurarLogging
from Extra.FuncionesArchivos import ObtenerArchivo


from libreria.MiStreanDeck import IniciarStreanDeck, MiStreanDeck
from libreria.MiTecladoMacro import MiTecladoMacro
# import libreria.MiTecladoMacro as MiTecladoMacro
# import libreria.MiStreanDeck as MiStreanDeck

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
                TecladoActual = MiTecladoMacro(Teclado['Nombre'], Teclado['Input'], Teclado['File'])
                if TecladoActual.Conectar():
                    self.ListaTeclados.append(TecladoActual)
            # self.ConfigurandoTeclados("")

    def CargarStreanDeck(self):
        """configurando StreanDeck"""
        self.ListaDeck = []
        if 'Deck' in self.Data:
            logger.info("Cargando StreamDeck")
            CargarDeck = IniciarStreanDeck(self.Data['Deck'])
            for Deck in CargarDeck:
                DeckActual = MiStreanDeck(Deck)
                self.ListaDeck.append(DeckActual)

    def ConfigurandoTeclados(self, Directorio):
        for Teclado in self.ListaTeclados:
            Teclado.ActualizarTeclas(Directorio)

    # def ConfigurandoSteanDeck(self, Direcotio):
    #     for Deck in slef.ListaDeck:
    #         print()
