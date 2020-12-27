# Librerias de ElGato
from StreamDeck.DeviceManager import DeviceManager

from Extra.Depuracion import Imprimir
from Extra.MiDeckImagen import ActualizarIcono, DefinirFuente
from Extra.Acciones import Accion, AgregarStreanDeck
from Extra.CargarData import AgregarComodines
# from Extra.TecladoMacro import TecTecladoMacro

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
            self.OBSConectado = False
            self.Folder = "Base"
            self.Data = Data
            if 'Comando' in self.Data:
                AgregarComodines(self.Data['Comando'], self.Deck.key_count())
            self.Deck.open()
            self.Deck.reset()

            if 'Brillo' in self.Data:
                self.Deck.set_brightness(self.Data['Brillo'])
            else:
                self.Deck.set_brightness(50)
                self.Data['Brillo'] = 50

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

    def CambiarBrillo(self, Incremento):
        self.Data['Brillo'] += Incremento
        if self.Data['Brillo'] > 100:
            self.Data['Brillo'] = 100
        elif self.Data['Brillo'] < 0:
            self.Data['Brillo'] = 0
        Imprimir(f"Intensidad Brillo StreamDeck - {self.Data['Brillo']}")
        self.Deck.set_brightness(self.Data['Brillo'])

    def ActualizarBoton(self, Deck, IndiceBoton, estado):
        IndiceBoton = IndiceBoton - self.DesfaceBoton
        if estado:
            if IndiceBoton < len(self.BotonActuales):
                Imprimir(f"Boton {IndiceBoton} - {self.BotonActuales[IndiceBoton]['Nombre']}")
                Accion(self.BotonActuales[IndiceBoton])
            else:
                Imprimir(f"Boton {IndiceBoton} - no programada")

    def BotonesSiquiente(self, Siquiente):
        if Siquiente:
            self.DesfaceBoton -= self.Deck.key_count()
        else:
            self.DesfaceBoton += self.Deck.key_count()

        if self.DesfaceBoton > 0:
            self.DesfaceBoton = 0
        elif -self.DesfaceBoton > len(self.BotonActuales):
            self.DesfaceBoton += self.Deck.key_count()

    def BuscarCarpeta(self, Nombre):
        ComandosFolder = self.Data['Comando']
        for Boton in range(len(ComandosFolder)):
            if ComandosFolder[Boton]['Nombre'] == Nombre:
                return Boton
        return -1

    def BuscarBoton(self, IdFolder, Nombre):
        if(IdFolder == -1):
            return -1
        else:
            BotonesFolder = self.Data['Comando'][IdFolder]['Key']
            for tecla in range(len(BotonesFolder)):
                if BotonesFolder[tecla]['Nombre'] == Nombre:
                    return tecla

    def CambiarEstadoBoton(self, IdFolder, IdBoton, Estado):
        self.Data['Comando'][IdFolder]['Key'][IdBoton]['Estado'] = Estado

    def EsEsena(self, IdFolder, IdEsena):
        if 'OBS' in self.Data['Comando'][IdFolder]['Key'][IdEsena]:
            if self.Data['Comando'][IdFolder]['Key'][IdEsena]['OBS'] == "Esena":
                return True
        return False
