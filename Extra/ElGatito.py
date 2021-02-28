from Extra.Depuracion import Imprimir

import Extra.TecladoMacro as TecladoMacros
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
                TecladoActual = TecladoMacros.TecladoMacro(Teclado['Nombre'], Teclado['Input'], Teclado['File'])
                if TecladoActual.Conectar():
                    self.ListaTeclados.append(TecladoActual)
            self.ConfigurandoTeclados("")

    def CargarStreanDeck(self):
        if 'Deck' in self.Data:
            DeckActual = MiStreanDeck.MiStreanDeck(self.Data['Deck'])
            self.ListaDeck = DeckActual.Conectar()

    def ConfigurandoTeclados(self, Directorio):
        for Teclado in self.ListaTeclados:
            Teclado.ActualizarTeclas(Directorio)
