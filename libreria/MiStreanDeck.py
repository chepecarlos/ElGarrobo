import logging


from StreamDeck.DeviceManager import DeviceManager

from libreria.FuncionesArchivos import ObtenerValor
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.MiDeckImagen import ActualizarIcono

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class MiStreanDeck(object):

    def __init__(self, Deck):
        self.Deck = Deck
        self.ID = Deck.ID
        self.Cantidad = Deck.key_count()
        self.Serial = Deck.Serial
        self.Nombre = Deck.Nombre
        self.File = Deck.File
        self.Base = Deck.Base

    def ActualizarIconos(self, acciones, Unido=False):
        logger.info(f"empezando a actualizar iconos {self.Nombre}")
        if Unido:
            logger.info(f"Desde {self.Base} hasta {self.Base+self.Cantidad}")
            for i in range(self.Cantidad):
                AccionAcual = self.AccionDibujar(acciones, i)
                if AccionAcual is not None:
                    ActualizarIcono(self.Deck, i, AccionAcual)
        else:
            pass

    def AccionDibujar(self, acciones, i):
        for accion in acciones:
            if 'key' in accion:
                if accion['key'] == i + self.Base:
                    return accion
        return


def IniciarStreanDeck(Datas, FuncionEvento):
    streamdecks = DeviceManager().enumerate()
    logger.info(f"Cargando StreamDeck - {len(streamdecks) if len(streamdecks) > 0 else 'No Conectado'}")
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
                DeckActual.Cantidad = DeckActual.key_count()
                DeckActual.ID = Data['id']
                DeckActual.Nombre = Data['nombre']
                DeckActual.File = Data['file']
                DeckActual.FuncionEvento = FuncionEvento
                DeckActual.set_key_callback(ActualizarBoton)
                ListaDeck.append(DeckActual)
                Data['encontado'] = True

    ListaDeck.sort(key=lambda x: x.ID, reverse=False)
    Cantidad_Base = 0
    for deck in ListaDeck:
        deck.Base = Cantidad_Base
        Cantidad_Base += deck.Cantidad

    for Data in Datas:
        if not Data['encontado']:
            logger.warning(f"No se encontro: {Data['nombre']} - {Data['serial']}")
    return ListaDeck


def ActualizarBoton(Deck, Key, estado):
    if estado:
        data = {"nombre": Deck.Nombre,
                "key": Key,
                "deck": True,
                "base": Deck.Base
                }
        Deck.FuncionEvento(data)
