from Extra.Depuracion import Imprimir
from Extra.MiStreanDeck import CargarStrean

import Extra.MiTecladoMacro as TecladoMacro
import Extra.MiStreanDeck as MiStreanDeck


class ElGatito(object):

    def __init__(self, Data):
        self.Data = Data
        Imprimir("Iniciando ElGatito")
        self.CargarTeclados()
        self.CargarStreanDeck()

    def CargarTeclados(self):
        if 'Teclados' in self.Data:
            self.ListaTeclados = []
            for Teclado in self.Data['Teclados']:
                TecladoActual = TecladoMacro.MiTecladoMacro(Teclado['Nombre'], Teclado['Input'], Teclado['File'])
                if TecladoActual.Conectar():
                    self.ListaTeclados.append(TecladoActual)
            self.ConfigurandoTeclados("")

    def CargarStreanDeck(self):
        self.ListaDeck = []
        if 'Deck' in self.Data:
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
