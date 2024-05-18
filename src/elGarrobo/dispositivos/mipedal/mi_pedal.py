# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

from elGarrobo.miLibrerias import ConfigurarLogging

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Transport.Transport import TransportError

logger = ConfigurarLogging(__name__)


class MiPedal(object):
    def __init__(self, data, evento):
        self.id = data.get("id")
        self.nombre = data.get("nombre")
        self.serial = data.get("serial")
        self.file = data.get("file")
        self.conectado = False
        self.deck = None
        self.evento = evento
        self.index = -1

    def conectar(self, indexUsados):
        streamdecks = DeviceManager().enumerate()
       
        for index, deck in enumerate(streamdecks):
            probarIndex = True
            for indexUsado in indexUsados:
                if index == indexUsado:
                    probarIndex = False

            if probarIndex:
                try:
                    self.deck = deck
                    self.deck.open()
                    if self.deck.get_serial_number() == self.serial and self.deck.deck_type() == "Stream Deck Pedal":
                        self.conectado = True
                        self.cantidad = self.deck.key_count()
                        self.deck.set_key_callback(self.actualizarBoton)
                        self.index = index
                        return self.index
                    else:
                        self.deck.close()
                except TransportError as error:
                    self.Conectado = False
                    self.Deck = None
                    logger.exception(f"Error 1 {error}")
                except Exception as error:
                    self.Conectado = False
                    self.Deck = None
                    logger.exception(f"Error 2 {error}")

    def actualizarBoton(self, Deck, Key, Estado):
        data = {
            "nombre": self.nombre,
            "key": Key,
            "estado": Estado,
        }
        self.evento(data)

    def desconectar(self):
        if self.conectado:
            logger.info(f"Pedal[Desconectando] - {self.nombre}")
            self.Conectado = False
            self.deck.reset()
            self.deck.close()
