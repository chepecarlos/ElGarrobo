import io

from PIL import Image
from PIL.Image import Image as ImageImage
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

    altoBarra = 100
    "Alto de la barra táctil"
    anchoBarra = 800
    "Ancho de la barra táctil"

    listaBotonesTouchscreen: list = list()
    "Lista de botones en touchscreen"

    cantidadBotonesTouchscreen: int = 0
    "Cantidad de botones en touchscreen"
    cantidadBotonesTouchscreenAnterior: int = 0
    "Cantidad de botones en touchscreen anterior para comparar cambios"

    listaBotonesTouchscreenViejas: list[dict] | None = None
    "lista de información de botones touchscreen viejas para comparar cambios"

    def __init__(self, dataConfiguracion: dict) -> None:
        """Inicializando Dispositivo de teclado

        Args:
            dataConfiguracion (dict): Datos de configuración del dispositivo
        """
        super().__init__(dataConfiguracion)
        self.nombre = dataConfiguracion.get("nombre", "streamdeckplus")
        self.listaBotonesTouchscreen = []
        self.listaBotonesTouchscreenViejas = None
        self.cantidadBotonesTouchscreen = 0
        self.cantidadBotonesTouchscreenAnterior = 0

    def conectar(self) -> bool:

        super().conectar()

        if self.conectado:
            self.deck.set_dial_callback(self.actualizarEncoderRotatorio)
            self.deck.set_touchscreen_callback(self.actualizarTouchScreen)
            self.cantidadDial = self.deck.DIAL_COUNT

        return self.conectado

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
        posicionX = value["x"]

        if self.cantidadBotonesTouchscreen <= 0:
            return

        botonPresionado = int(posicionX / (self.anchoBarra / self.cantidadBotonesTouchscreen)) + 1

        if evt_type == TouchscreenEventType.SHORT:
            self.buscarAccion(f"touchscreen_{botonPresionado}", self.estadoTecla.PRESIONADA)
        elif evt_type == TouchscreenEventType.LONG:

            print("Long touch @ " + str(value["x"]) + "," + str(value["y"]))

        elif evt_type == TouchscreenEventType.DRAG:

            posicionXFinal = value["x_out"]

            if abs(posicionX - posicionXFinal) > self.anchoBarra / 20:
                if posicionX > posicionXFinal:
                    self.buscarAccion(f"deslizar_izquierda_{botonPresionado}")
                else:
                    self.buscarAccion(f"deslizar_derecha_{botonPresionado}")

    def actualizarIconos(self) -> None:
        """Actualiza los iconos del touchscreen del Stream Deck Plus."""

        super().actualizarIconos()

        if self.deck is None or not self.deck.is_open():
            self.conectado = False
            return

        actualizarTouchscreen: bool = False

        if self.cantidadBotonesTouchscreen <= 0:
            self.generarImagenTouchscreen()
            return

        if self.listaBotonesTouchscreenViejas is None or len(self.listaBotonesTouchscreenViejas) != self.cantidadBotonesTouchscreen:
            self.listaBotonesTouchscreenViejas = [
                {
                    "imagen": None,
                    "titulo": None,
                    "gif": None,
                }
                for _ in range(self.cantidadBotonesTouchscreen)
            ]
            actualizarTouchscreen = True

        for boton in range(0, len(self.listaBotonesTouchscreen)):
            accionActual: dict = self.listaBotonesTouchscreen[boton]
            accionVieja: dict = self.listaBotonesTouchscreenViejas[boton]

            imagenActual: str | None = self.buscarDirecionImagen(accionActual)
            tituloActual: str | None = self.buscarTitulo(accionActual)

            imagenVieja: str | None = accionVieja.get("imagen")
            tituloViejo: str | None = accionVieja.get("titulo")

            if imagenActual == imagenVieja and tituloActual == tituloViejo:
                continue
            else:
                accionVieja["imagen"] = imagenActual
                accionVieja["titulo"] = tituloActual
                actualizarTouchscreen = True

        if not actualizarTouchscreen:
            return

        self.generarImagenTouchscreen()

    def generarImagenTouchscreen(self) -> None:
        """Genera y actualiza la imagen del touchscreen del Stream Deck Plus."""

        imagenBase = Image.new("RGB", (self.anchoBarra, self.altoBarra))

        print("Generando imagen del touchscreen con " + str(self.cantidadBotonesTouchscreen) + " botones.")

        if self.cantidadBotonesTouchscreen > 0:
            anchoBoton = int(self.anchoBarra / self.cantidadBotonesTouchscreen)

            for boton in range(0, len(self.listaBotonesTouchscreen)):

                imagenLimpia: ImageImage = Image.new("RGB", (anchoBoton, self.altoBarra))
                accionActual: dict = self.listaBotonesTouchscreen[boton]

                imagenLista: ImageImage = self.obtenerImagen(imagenLimpia, accionActual)

                posicionX: int = int((boton + 0.5) * self.anchoBarra / self.cantidadBotonesTouchscreen - anchoBoton / 2)
                posicionY: int = 0
                imagenBase.paste(imagenLista, (posicionX, posicionY))

        img_bytes = io.BytesIO()
        imagenBase.save(img_bytes, format="JPEG")
        touchscreen_image_bytes = img_bytes.getvalue()

        self.deck.set_touchscreen_image(touchscreen_image_bytes, 0, 0, self.anchoBarra, self.altoBarra)

    def actualizar(self) -> None:

        listaBotonesTouchscreenNueva = [d for d in self.listaAcciones if str(d.get("key", "")).startswith("touchscreen_")]
        listaBotonesTouchscreenNueva.sort(key=lambda x: int(x["key"].split("_")[1]))

        cantidadBotonesTouchscreenNueva = len(listaBotonesTouchscreenNueva)
        touchscreenCambio = cantidadBotonesTouchscreenNueva != self.cantidadBotonesTouchscreen or listaBotonesTouchscreenNueva != self.listaBotonesTouchscreen

        if self.recargar or touchscreenCambio:
            self.listaBotonesTouchscreen = listaBotonesTouchscreenNueva
            self.cantidadBotonesTouchscreenAnterior = self.cantidadBotonesTouchscreen
            self.cantidadBotonesTouchscreen = cantidadBotonesTouchscreenNueva

            if self.cantidadBotonesTouchscreen != self.cantidadBotonesTouchscreenAnterior:
                self.listaBotonesTouchscreenViejas = None

            self.actualizarIconos()
        super().actualizar()
