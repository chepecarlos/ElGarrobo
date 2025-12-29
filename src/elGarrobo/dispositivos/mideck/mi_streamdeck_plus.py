from StreamDeck.Devices.StreamDeck import DialEventType, TouchscreenEventType

from elGarrobo.dispositivos.mideck.mi_streamdeck import MiStreamDeck


class MiStreamDeckPlus(MiStreamDeck):

    modulo = "streamdeckplus"
    tipo = "streamdeckplus"
    compatibles = ["Stream Deck +"]

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

    def actualizarEncoderRotatorio(self, deck, dial, event, value):
        if event == DialEventType.PUSH:
            print(f"dial pushed: {dial+1} state: {value}")
        elif event == DialEventType.TURN:
            print(f"dial {dial+1} turned: {value}")
        elif event == DialEventType.TURN:
            print(f"dial {dial+1} turned: {value}")

    def actualizarTouchScreen(self, deck, evt_type, value):
        if evt_type == TouchscreenEventType.SHORT:
            print("Short touch @ " + str(value["x"]) + "," + str(value["y"]))

        elif evt_type == TouchscreenEventType.LONG:

            print("Long touch @ " + str(value["x"]) + "," + str(value["y"]))

        elif evt_type == TouchscreenEventType.DRAG:

            print("Drag started @ " + str(value["x"]) + "," + str(value["y"]) + " ended @ " + str(value["x_out"]) + "," + str(value["y_out"]))
