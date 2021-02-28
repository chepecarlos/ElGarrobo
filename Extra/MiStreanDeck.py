from StreamDeck.DeviceManager import DeviceManager

from Extra.Depuracion import Imprimir


class MiStreanDeck(object):

    def __init__(self, Data):
        self.Data = Data

    def Conectar(self):
        streamdecks = DeviceManager().enumerate()
        ListaDeck = []
        for deck in streamdecks:
            DeckActual = deck
            DeckActual.open()
            DeckActual.reset()
            DeckActual.set_brightness(50)
            Encontrado = False
            for Data in self.Data:
                if Data['Serial'] == DeckActual.get_serial_number():
                    print(f"Abriendo : {DeckActual.DECK_TYPE} -  {DeckActual.get_serial_number()}")
                    DeckActual.Serial = DeckActual.get_serial_number()
                    DeckActual.set_key_callback(self.ActualizarBoton)
                    ListaDeck.append(DeckActual)
                    Encontrado = True
            if not Encontrado:
                DeckActual = None
        return ListaDeck

    def ActualizarBoton(self, Deck, IndiceBoton, estado):
        print(f"Serial {Deck.id()} {Deck.Serial} Key {IndiceBoton} [{estado}]")
