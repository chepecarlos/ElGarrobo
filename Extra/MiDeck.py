# Librerias de ElGato
from StreamDeck.DeviceManager import DeviceManager

from Extra.Depuracion import Imprimir
from Extra.MiDeckImagen import ActualizarIcono, DefinirFuente, DefinirDesface


class MiDeck(object):
    """docstring for MiMQTT."""

    def __init__(self, Data):
        self.Data = Data
        self.DesfaceBoton = 0
        self.ConectadoMiDeck = False
        streamdecks = DeviceManager().enumerate()
        Imprimir(f"Cargando StreamDeck - {'Encontrado' if len(streamdecks) > 0 else 'No Conectado'}")

        for index, deck in enumerate(streamdecks):
            self.Deck = deck
            self.Deck.open()
            self.Deck.reset()

            if 'Brillo' in self.Data:
                deck.set_brightness(self.Data['Brillo'])
            else:
                deck.set_brightness(50)

            Imprimir(f"Abriendo '{deck.deck_type()}' (Numero Serial: '{deck.get_serial_number()}')")

        if 'Fuente' in self.Data:
            DefinirFuente(self.Data['Fuente'])
        else:
            Imprimir("Fuente no asignada")
            self.Cerrar()

        self.BotonActuales = self.Data['Comando']
        DefinirDesface()
        self.ActualizarTodasImagenes()

        self.Deck.set_key_callback(self.ActualizarBoton)

    def ActualizarTodasImagenes(self):
        for IndiceBoton in range(len(self.BotonActuales)):
            ActualizarIcono(self.Deck, self.BotonActuales, IndiceBoton, self.Data)

    def Cerrar(self):
        self.Deck.close()

    def ActualizarBoton(self, Deck, IndiceBoton, estado):
        IndiceBoton = IndiceBoton - self.DesfaceBoton
        if estado:
            if IndiceBoton < len(self.BotonActuales):
                Imprimir(f"Boton {IndiceBoton} - {self.BotonActuales[IndiceBoton]['Nombre']}")
                # ActualizarAccion(teclas[IndiceBoton])
            else:
                Imprimir(f"Boton {IndiceBoton} - no programada")
