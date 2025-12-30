import io

from PIL import Image
from StreamDeck.Devices.StreamDeck import DialEventType, TouchscreenEventType

from elGarrobo.dispositivos.mideck.mi_streamdeck import MiStreamDeck
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__)


class MiStreamDeckPlus(MiStreamDeck):

    modulo = "streamdeckplus"
    tipo = "streamdeckplus"
    compatibles = ["Stream Deck +"]

    baseDial: int = 0
    desfaceDial: int = 0
    cantidadDial: int = 0

    def __init__(self, dataConfiguracion: dict) -> None:
        """Inicializando Dispositivo de teclado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """
        super().__init__(dataConfiguracion)
        self.nombre = dataConfiguracion.get("nombre", "streamdeckplus")

    def conectar(self) -> None:

        super().conectar()

        if self.conectado:
            self.deck.set_dial_callback(self.actualizarEncoderRotatorio)
            self.deck.set_touchscreen_callback(self.actualizarTouchScreen)
            self.cantidadDial = self.deck.DIAL_COUNT

    def actualizarEncoderRotatorio(self, deck, numeroDial, evento, estado):
        numeroDial += 1
        if evento == DialEventType.PUSH:
            if estado:
                self.buscarAccion(f"dial_{numeroDial}", self.estadoTecla.PRESIONADA)
            else:
                self.buscarAccion(f"dial_{numeroDial}", self.estadoTecla.LIBERADA)
        elif evento == DialEventType.TURN:
            if estado > 0:
                self.buscarAccion(f"dial_derecho_{numeroDial}", self.estadoTecla.PRESIONADA, fuerza=estado)
            else:
                self.buscarAccion(f"dial_izquierdo_{numeroDial}", self.estadoTecla.PRESIONADA, fuerza=abs(estado))

    def actualizarTouchScreen(self, deck, evt_type, value):
        if evt_type == TouchscreenEventType.SHORT:
            print("Short touch @ " + str(value["x"]) + "," + str(value["y"]))

        elif evt_type == TouchscreenEventType.LONG:

            print("Long touch @ " + str(value["x"]) + "," + str(value["y"]))

        elif evt_type == TouchscreenEventType.DRAG:

            print("Drag started @ " + str(value["x"]) + "," + str(value["y"]) + " ended @ " + str(value["x_out"]) + "," + str(value["y_out"]))

    def actualizarIconos(self) -> None:

        super().actualizarIconos()

        img = Image.new("RGB", (800, 100), "red")

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        touchscreen_image_bytes = img_bytes.getvalue()

        self.deck.set_touchscreen_image(touchscreen_image_bytes, 0, 0, 800, 100)
