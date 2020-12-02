# Librerias de ElGato
from StreamDeck.DeviceManager import DeviceManager

from Extra.Depuracion import Imprimir
from Extra.MiDeckImagen import ActualizarIcono, DefinirFuente
from Extra.Acciones import RealizarAccion, AgregarStreanDeck
from Extra.CargarData import AgregarComodines


class MiDeck(object):
    """docstring for MiMQTT."""

    def __init__(self, Data):
        self.ConectadoMiDeck = False
        streamdecks = DeviceManager().enumerate()
        Imprimir(f"Cargando StreamDeck - {'Encontrado' if len(streamdecks) > 0 else 'No Conectado'}")

        for index, deck in enumerate(streamdecks):
            self.Deck = deck
            self.ConectadoMiDeck = True
            self.DesfaceBoton = 0
            self.Folder = "Base"
            self.Data = Data
            if 'Comando' in self.Data:
                AgregarComodines(self.Data['Comando'], self.Deck.key_count())
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

        AgregarStreanDeck(self)
        self.BotonActuales = self.Data['Comando']
        self.ActualizarTodasImagenes()

        self.Deck.set_key_callback(self.ActualizarBoton)

    def ActualizarTodasImagenes(self, Limpiar=False):
        if(Limpiar):
            for IndiceBoton in range(self.Deck.key_count()):
                ActualizarIcono(self, IndiceBoton, Limpiar)
        for IndiceBoton in range(len(self.BotonActuales)):
            ActualizarIcono(self, IndiceBoton)

    def Cerrar(self):
        self.Deck.close()

    def ActualizarBoton(self, Deck, IndiceBoton, estado):
        IndiceBoton = IndiceBoton - self.DesfaceBoton
        if estado:
            if IndiceBoton < len(self.BotonActuales):
                Imprimir(f"Boton {IndiceBoton} - {self.BotonActuales[IndiceBoton]['Nombre']}")
                RealizarAccion(self.BotonActuales[IndiceBoton])
            else:
                Imprimir(f"Boton {IndiceBoton} - no programada")

    def BotonesSiquiente(self, Siquiente):
        if Siquiente:
            self.DesfaceBoton -= self.Deck.key_count()
        else:
            self.DesfaceBoton += self.Deck.key_count()

    def BuscarCarpeta(self, Nombre):
        ComandosFolder = self.Data['Comando']
        for Boton in range(len(ComandosFolder)):
            if(ComandosFolder[Boton]['Nombre'] == Nombre):
                return Boton
        return -1

    def BuscarBoton(self, IdFolder, Nombre):
        if(IdFolder == -1):
            return -1
        else:
            BotonesFolder = self.Data['Comando'][IdFolder]['Key']
            for tecla in range(len(BotonesFolder)):
                if(BotonesFolder['Nombre'] == Nombre):
                    return tecla
