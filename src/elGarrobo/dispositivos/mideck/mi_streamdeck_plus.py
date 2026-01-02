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

    listaBotonesTouchscreen: list = list()
    "Lista de botones en touchscreen"

    cantidadBotonesTouchscreen: int = 0
    "Cantidad de botones en touchscreen"

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
            posicionX = value["x"]
            botonPresionado = int(posicionX / (800 / self.cantidadBotonesTouchscreen)) + 1
            self.buscarAccion(f"touchscreen_{botonPresionado}", self.estadoTecla.PRESIONADA)
        elif evt_type == TouchscreenEventType.LONG:

            print("Long touch @ " + str(value["x"]) + "," + str(value["y"]))

        elif evt_type == TouchscreenEventType.DRAG:

            print("Drag started @ " + str(value["x"]) + "," + str(value["y"]) + " ended @ " + str(value["x_out"]) + "," + str(value["y_out"]))

    def actualizarIconos(self) -> None:

        super().actualizarIconos()

        altoBarra = 100
        anchoBarra = 800

        imagenBase = Image.new("RGB", (anchoBarra, altoBarra))
        anchoBoton = int(anchoBarra / self.cantidadBotonesTouchscreen)

        for boton in range(0, len(self.listaBotonesTouchscreen)):

            imagenLimpia: Image.Image = Image.new("RGB", (anchoBoton, altoBarra))
            accionActual: dict = self.listaBotonesTouchscreen[boton]

            imagenLista: Image.Image = self.obtenerImagen(imagenLimpia, accionActual)

            posicionX: int = int((boton + 0.5) * 800 / self.cantidadBotonesTouchscreen - anchoBoton / 2)
            posicionY: int = 0
            imagenBase.paste(imagenLista, (posicionX, posicionY))

        img_bytes = io.BytesIO()
        imagenBase.save(img_bytes, format="JPEG")
        touchscreen_image_bytes = img_bytes.getvalue()

        self.deck.set_touchscreen_image(touchscreen_image_bytes, 0, 0, 800, 100)

    def actualizar(self) -> None:
        super().actualizar()

        self.listaBotonesTouchscreen.clear()
        self.listaBotonesTouchscreen.extend([d for d in self.listaAcciones if str(d.get("key", "")).startswith("touchscreen_")])
        self.listaBotonesTouchscreen.sort(key=lambda x: int(x["key"].split("_")[1]))
        self.cantidadBotonesTouchscreen = len(self.listaBotonesTouchscreen)

        self.actualizarIconos()
