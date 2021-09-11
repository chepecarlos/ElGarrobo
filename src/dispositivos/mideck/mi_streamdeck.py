# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Transport.Transport import TransportError

from .mi_deck_gif import DeckGif
from .mi_deck_imagen import ActualizarIcono, LimpiarIcono
from .mi_deck_extra import BuscarDirecionImagen

from MiLibrerias import ConfigurarLogging
from MiLibrerias import ObtenerValor

logger = ConfigurarLogging(__name__)


class MiStreamDeck(object):

    def __init__(self, Data, Evento, Base):
        self.ID = Data['id']
        self.Nombre = Data['nombre']
        self.Serial = Data['serial']
        self.File = Data['file']
        self.Conectado = False
        self.Deck = None
        self.DeckGif = None
        self.Cantidad = 0
        self.Base = Base
        self.Evento = Evento

    def Conectar(self):
        streamdecks = DeviceManager().enumerate()

        # TODO: Cambiar metodo para cargar StreanDeks
        for index, deck in enumerate(streamdecks):
            try:
                self.Deck = deck
                self.Deck.open()
                self.Deck.reset()
                if self.Deck.get_serial_number() == self.Serial:
                    self.Conectado = True
                    self.Cantidad = self.Deck.key_count()
                    Brillo = ObtenerValor("data/streamdeck.json", "brillo")
                    self.Deck.set_brightness(Brillo)
                    self.DeckGif = DeckGif(self.Deck)
                    self.DeckGif.start()
                    self.Deck.set_key_callback(self.ActualizarBoton)
                    return
                else:
                    self.Deck.close()

            except TransportError as error:
                self.Conectado = False
                self.Deck = None
                logger.exception(f"Error 1 {error}")
            except Exception as error:
                self.Conectado = False
                self.Deck = None
                logger.exception(f"Error 2 {error}")

    def ActualizarIconos(self, acciones, desface, Unido=False):
        """Refesca iconos, tomando en cuenta pagina actual."""
        if self.Conectado:
            logger.info(f"Deck[Dibujar] {self.Nombre}")
            if Unido:
                for i in range(self.Cantidad):
                    key_desface = i + self.Base + desface
                    Dibujar = list(filter(lambda accion: accion['key'] == key_desface, acciones))
                    # TODO: Cargar primer los Gifs # if AccionAcual is not None:
                    
                    if Dibujar:
                        AccionAcual = Dibujar[0]
                        # if 'imagen' in AccionAcual:
                            # DirecionImagen = AccionAcual['imagen']
                        DirecionImagen = BuscarDirecionImagen(AccionAcual)
                        if DirecionImagen is not None and DirecionImagen.endswith(".gif"):
                            self.DeckGif.ActualizarGif(i, AccionAcual)
                        else:
                            ActualizarIcono(self.Deck, i, AccionAcual)
                        # if 'gif' in AccionAcual:
                        #     self.DeckGif.ActualizarGif(i, AccionAcual)
                        # else:
                        #     ActualizarIcono(self.Deck, i, AccionAcual)
            else:
                pass

    def Limpiar(self):
        """Borra iconos de todo los botones de StreamDeck."""
        if self.Conectado:
            self.DeckGif.Limpiar()
            for i in range(self.Cantidad):
                LimpiarIcono(self.Deck, i)

    def Brillo(self, Brillo):
        """Cambia brillo de StreamDeck."""
        if self.Conectado:
            self.Deck.set_brightness(Brillo)

    def CambiarFolder(self, Folder):
        if self.Conectado:
            self.Deck.Folder = Folder

    def ActualizarBoton(self, Deck, Key, Estado):
        data = {"nombre": self.Nombre,
                "key": Key,
                "deck": True,
                "base": self.Base,
                "estado": Estado
                }
        self.Evento(data)
    
    def Desconectar(self):
        if self.Conectado:
            logger.info(f"Deck[Desconectando] - {self.Nombre}")
            self.DeckGif.Desconectar()
            self.Conectado = False
            self.Deck.reset()
            self.Deck.close()

def IniciarStreamDeck(Datas, FuncionEvento):
    streamdecks = DeviceManager().enumerate()
    logger.info(
        f"Cargando StreamDeck - {len(streamdecks) if len(streamdecks) > 0 else 'No Conectado'}")
    ListaDeck = []
    for Data in Datas:
        Data['Encontado'] = False

    for deck in streamdecks:
        DeckActual = deck
        DeckActual.open()
        DeckActual.reset()
        Brillo = ObtenerValor("data/streamdeck.json", "brillo")
        DeckActual.set_brightness(Brillo)

        for Data in Datas:
            if Data['serial'] == DeckActual.get_serial_number():
                logger.info(
                    f"Conectando: {Data['nombre']} - {DeckActual.get_serial_number()}")
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
            logger.warning(
                f"No se encontro: {Data['nombre']} - {Data['serial']}")
    return ListaDeck


def ActualizarBoton(Deck, Key, Estado):
    data = {"nombre": Deck.Nombre,
            "key": Key,
            "deck": True,
            "base": Deck.Base,
            "estado": Estado
            }
    Deck.FuncionEvento(data)
