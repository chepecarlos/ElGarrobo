from StreamDeck.DeviceManager import DeviceManager

from Extra.Depuracion import Imprimir
from Extra.FuncionesArchivos import ObtenerDato


class MiStreanDeck(object):

    def __init__(self, Deck):
        self.Deck = Deck
        self.Serial = Deck.Serial
        self.Nombre = Deck.Nombre
        self.File = Deck.File

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
                    DeckActual.Nombre = Data['Nombre']
                    DeckActual.File = Data['File']
                    DeckActual.set_key_callback(self.ActualizarBoton)
                    ListaDeck.append(DeckActual)
                    Encontrado = True
            if not Encontrado:
                print(f"No se encontro {Data['Serial']}")
                DeckActual = None
        return ListaDeck

    def ActualizarBoton(self, Deck, IndiceBoton, estado):
        print(f"Serial {Deck.id()} {Deck.Serial} Key {IndiceBoton} [{estado}]")


def CargarStrean(Datas):
    streamdecks = DeviceManager().enumerate()
    ListaDeck = []
    for Data in Datas:
        Data['Encontado'] = False

    for deck in streamdecks:
        DeckActual = deck
        DeckActual.open()
        DeckActual.reset()
        Brillo = ObtenerDato("/Data/StreanDeck.json", "Brillo")
        DeckActual.set_brightness(Brillo)
        for Data in Datas:
            if Data['Serial'] == DeckActual.get_serial_number():
                print(f"Encontrado: {DeckActual.DECK_TYPE} -  {DeckActual.get_serial_number()}")
                DeckActual.Serial = DeckActual.get_serial_number()
                DeckActual.Nombre = Data['Nombre']
                DeckActual.File = Data['File']
                DeckActual.set_key_callback(ActualizarBoton)
                ListaDeck.append(DeckActual)
                Data['Encontado'] = True

    for Data in Datas:
        if not Data['Encontado']:
            print(f"No se encontro {Data['Serial']}")
    return ListaDeck


def ActualizarBoton(Deck, IndiceBoton, estado):
    print(f"StreanDeck {Deck.Nombre} {Deck.Serial} Key {IndiceBoton} [{estado}]")
