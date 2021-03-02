import logging


from StreamDeck.DeviceManager import DeviceManager

from libreria.FuncionesArchivos import ObtenerValor
from libreria.FuncionesLogging import ConfigurarLogging

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class MiStreanDeck(object):

    def __init__(self, Deck):
        self.Deck = Deck
        self.Serial = Deck.Serial
        self.Nombre = Deck.Nombre
        self.File = Deck.File


def IniciarStreanDeck(Datas, FuncionEvento):
    streamdecks = DeviceManager().enumerate()
    ListaDeck = []
    for Data in Datas:
        Data['Encontado'] = False

    for deck in streamdecks:
        DeckActual = deck
        DeckActual.open()
        DeckActual.reset()
        Brillo = ObtenerValor("data/streandeck.json", "brillo")
        DeckActual.set_brightness(Brillo)
        for Data in Datas:
            if Data['serial'] == DeckActual.get_serial_number():
                logger.info(f"Conectando: {Data['nombre']} - {DeckActual.get_serial_number()}")
                DeckActual.Serial = DeckActual.get_serial_number()
                DeckActual.Nombre = Data['nombre']
                DeckActual.File = Data['file']
                DeckActual.FuncionEvento = FuncionEvento
                DeckActual.set_key_callback(ActualizarBoton)
                ListaDeck.append(DeckActual)
                Data['encontado'] = True

    for Data in Datas:
        if not Data['encontado']:
            logger.warning(f"No se encontro: {Data['nombre']} - {Data['serial']}")
    return ListaDeck


def ActualizarBoton(Deck, Key, estado):
    if estado:
        data = {"nombre": Deck.Nombre,
                "key": Key}
        Deck.FuncionEvento(data)
