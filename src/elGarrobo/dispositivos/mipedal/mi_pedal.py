# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Transport.Transport import TransportError

from elGarrobo.dispositivos.dispositivoBase import dispositivoBase
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


class MiPedal(dispositivoBase):

    def __init__(self, data: dict, ejecutarAcción: callable, folderPerfil: str):
        self.id = data.get("id")
        nombre: str = data.get("nombre")
        archivo: str = data.get("archivo")
        self.serial: str = data.get("serial")
        self.conectado: bool = False
        self.deck = None
        self.index: int = -1
        super().__init__(nombre, self.serial, archivo, folderPerfil)
        self.ejecutarAcción: callable = ejecutarAcción
        self.tipo = "pedal"

    def conectar(self, indexUsados) -> int:
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
                    self.deck.reset()
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
                    self.deck = None
                    logger.exception(f"Error 1 {error}")
                    logger.error(f"Error 1 {error}")
                except Exception as error:
                    self.Conectado = False
                    self.deck = None
                    logger.exception(f"Error 2 {error}")
                    logger.error(f"Error 2 {error}")

    def actualizarBoton(self, Deck, Key: int, Estado: bool):
        data = {
            "nombre": self.nombre,
            "key": str(Key + 1),
            "estado": Estado,
        }
        self.buscarAcción(data)
        # print(f"Se precioso {self.tipo} {data}")
        # print(f"Lista acciones {self.listaAcciones}")
        # self.evento(data)

    def desconectar(self):
        if self.conectado:
            logger.info(f"Pedal[Desconectando] - {self.nombre}")
            self.Conectado = False
            self.deck.reset()
            self.deck.close()
