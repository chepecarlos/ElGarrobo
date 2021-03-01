import logging


from StreamDeck.DeviceManager import DeviceManager

from libreria.FuncionesArchivos import ObtenerDato
from libreria.FuncionesLogging import ConfigurarLogging

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class MiStreanDeck(object):

    def __init__(self, Deck):
        self.Deck = Deck
        self.Serial = Deck.Serial
        self.Nombre = Deck.Nombre
        self.File = Deck.File

    def ActualizarBoton(self, Deck, IndiceBoton, estado):
        logging.debug(f"Serial {Deck.id()} {Deck.Serial} Key {IndiceBoton} [{estado}]")
        print(f"Serial {Deck.id()} {Deck.Serial} Key {IndiceBoton} [{estado}]")


def IniciarStreanDeck(Datas):
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
                logger.info(f"Conectando: {Data['Nombre']} - {DeckActual.get_serial_number()}")
                DeckActual.Serial = DeckActual.get_serial_number()
                DeckActual.Nombre = Data['Nombre']
                DeckActual.File = Data['File']
                DeckActual.set_key_callback(ActualizarBoton)
                ListaDeck.append(DeckActual)
                Data['Encontado'] = True

    for Data in Datas:
        if not Data['Encontado']:
            logger.warning(f"No se encontro: {Data['Nombre']} - {Data['Serial']}")
    return ListaDeck


def ActualizarBoton(Deck, IndiceBoton, estado):
    logger.debug(f"StreanDeck {Deck.Nombre} {Deck.Serial} Key {IndiceBoton} [{estado}]")
