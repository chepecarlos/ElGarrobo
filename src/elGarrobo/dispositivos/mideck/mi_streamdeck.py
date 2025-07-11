# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html

import time

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Transport.Transport import TransportError

from elGarrobo.dispositivos.dispositivoBase import dispositivoBase
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor

from .mi_deck_extra import BuscarDirecionImagen
from .mi_deck_gif import DeckGif
from .mi_deck_imagen import ActualizarIcono, LimpiarIcono

logger = ConfigurarLogging(__name__)


class MiStreamDeck(dispositivoBase):

    Folder: str = None

    def __init__(self, Data, Evento, Base):
        self.id = Data["id"]
        self.Nombre: str = Data["nombre"]
        self.Serial: str = Data["serial"]
        self.File: str = Data["file"]
        self.Folder: str = None
        self.Conectado: bool = False
        self.Deck = None
        self.DeckGif = None
        self.Cantidad: int = 0
        self.layout = None
        self.Base = Base
        self.Evento = Evento
        self.ultimoDibujo = None
        self.tiempoDibujar: float = 0.4
        self.index: int = -1
        self.archivoImagen = None

    def Conectar(self, indexUsados):
        streamdecks = DeviceManager().enumerate()

        # TODO: Cambiar metodo para cargar StreanDeks
        for index, deck in enumerate(streamdecks):
            probarIndex = True
            for indexUsado in indexUsados:
                if index == indexUsado:
                    probarIndex = False

            if probarIndex:
                try:
                    self.Deck = deck
                    self.Deck.open()
                    self.Deck.reset()
                    if self.Deck.get_serial_number() == self.Serial:
                        self.Conectado = True
                        self.Cantidad = self.Deck.key_count()
                        self.layout = self.Deck.key_layout()
                        Brillo = ObtenerValor("data/streamdeck.json", "brillo")
                        # Todo: brillo no es un int
                        self.Deck.set_brightness(Brillo)
                        self.DeckGif = DeckGif(self.Deck, self.Folder)
                        self.DeckGif.start()
                        self.Deck.set_key_callback(self.ActualizarBoton)
                        self.index = index
                        return self.index
                    else:
                        self.Deck.close()

                except TransportError as error:
                    self.Conectado = False
                    self.Deck = None
                    logger.exception(f"Error 1 StreamDeck {error}")
                except Exception as error:
                    self.Conectado = False
                    self.Deck = None
                    logger.exception(f"Error 2 StreamDeck {error}")

    def ActualizarIconos(self, acciones: dict, desface: int, Unido: bool=False):
        """Refresca iconos, tomando en cuenta pagina actual."""
        if not self.Conectado:
            return

        if self.archivoImagen is None:
            self.archivoImagen = list()
            for _ in range(self.Cantidad):
                self.archivoImagen.append("")

        if self.Deck is None or not self.Deck.is_open():
            self.Conectado = False
            return

        tiempoActual = time.time()

        if self.ultimoDibujo is None:
            self.ultimoDibujo = -self.tiempoDibujar

        if tiempoActual - self.ultimoDibujo < self.tiempoDibujar:
            print(tiempoActual - self.ultimoDibujo, self.tiempoDibujar)
            return

        logger.info(f"Deck[Dibujar] {self.Nombre}")
        if Unido:
            for i in range(self.Cantidad):
                key_desface = i + self.Base + desface
                dibujar = list(filter(lambda accion: accion["key"] == key_desface, acciones))
                # TODO: Cargar primer los Gifs # if AccionAcual is not None:

                if dibujar:
                    accionAcual = dibujar[0]

                    if accionAcual.get("imagen"):
                        rutaImagenAcutal = accionAcual.get("imagen")
                        if rutaImagenAcutal == self.archivoImagen[i]:
                            continue
                        self.archivoImagen[i] = rutaImagenAcutal

                    DirecionImagen = BuscarDirecionImagen(accionAcual)
                    if DirecionImagen is not None and DirecionImagen.endswith(".gif"):
                        self.DeckGif.ActualizarGif(i, accionAcual, self.Folder)
                    else:
                        ActualizarIcono(self.Deck, i, accionAcual, self.Folder)

    def Limpiar(self):
        """Borra iconos de todo los botones de StreamDeck."""
        if self.Conectado:
            self.DeckGif.Limpiar()
            for i in range(self.Cantidad):
                LimpiarIcono(self.Deck, i)
            self.archivoImagen = None

    def Brillo(self, Brillo):
        """Cambia brillo de StreamDeck."""
        if self.Conectado:
            self.Deck.set_brightness(Brillo)

    def CambiarFolder(self, Folder):
        logger.debug(f"Entrando a {Folder}")
        self.Folder = Folder
        self.ultimoDibujo = -self.tiempoDibujar

    def ActualizarBoton(self, Deck, Key, Estado):
        # TODO: agregar estado precionsado y soltar
        data = {"nombre": self.Nombre, "key": Key, "deck": True, "base": self.Base, "estado": Estado}
        self.Evento(data)

    def Desconectar(self):
        if self.Conectado:
            logger.info(f"Deck[Desconectando] - {self.Nombre}")
            self.DeckGif.Desconectar()
            self.Conectado = False
            self.Deck.reset()
            self.Deck.close()
            
    def __str__(self):
        return f"MiStreamDeck(id={self.id}, nombre={self.Nombre}, serial={self.Serial}, layout={self.layout})"


def IniciarStreamDeck(Datas, FuncionEvento):
    streamdecks = DeviceManager().enumerate()
    logger.info(f"Cargando StreamDeck - {len(streamdecks) if len(streamdecks) > 0 else 'No Conectado'}")
    ListaDeck = []
    for Data in Datas:
        Data["Encontado"] = False

    for deck in streamdecks:
        DeckActual = deck
        DeckActual.open()
        DeckActual.reset()
        Brillo = ObtenerValor("data/streamdeck.json", "brillo")
        DeckActual.set_brightness(Brillo)

        for Data in Datas:
            if Data["serial"] == DeckActual.get_serial_number():
                logger.info(f"Conectando: {Data['nombre']} - {DeckActual.get_serial_number()}")
                DeckActual.Serial = DeckActual.get_serial_number()
                DeckActual.Cantidad = DeckActual.key_count()
                DeckActual.id = Data["id"]
                DeckActual.Nombre = Data["nombre"]
                DeckActual.File = Data["file"]
                DeckActual.FuncionEvento = FuncionEvento
                DeckActual.set_key_callback(ActualizarBoton)
                ListaDeck.append(DeckActual)
                Data["encontado"] = True

    ListaDeck.sort(key=lambda x: x.id, reverse=False)
    Cantidad_Base = 0
    for deck in ListaDeck:
        deck.Base = Cantidad_Base
        Cantidad_Base += deck.Cantidad

    for Data in Datas:
        if not Data["encontado"]:
            logger.warning(f"No se encontro: {Data['nombre']} - {Data['serial']}")
    return ListaDeck


def ActualizarBoton(Deck, Key, Estado):
    data = {"nombre": Deck.Nombre, "key": Key, "deck": True, "base": Deck.Base, "estado": Estado}
    Deck.FuncionEvento(data)
