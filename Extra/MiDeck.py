# Librerias de ElGato
from StreamDeck.DeviceManager import DeviceManager

from Extra.Depuracion import Imprimir
from Extra.MiDeckImagen import ActualizarIcono, DefinirFuente, IniciarAnimacion
from Extra.Acciones import Accion, AgregarStreanDeck
from Extra.CargarData import AgregarComodines
import Extra.TecladoMacro as TecladoMacros


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
            if 'StreamDeck' in self.Data:
                AgregarComodines(self.Data['StreamDeck'], self.Deck.key_count())
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

        self.CargarTeclados()
        AgregarStreanDeck(self)
        self.BotonActuales = self.Data['StreamDeck']
        IniciarAnimacion(self)
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
        ComandosFolder = self.Data['StreamDeck']
        for Boton in range(len(ComandosFolder)):
            if ComandosFolder[Boton]['Nombre'] == Nombre:
                return Boton
        return -1

    def BuscarBoton(self, IdFolder, Nombre):
        if(IdFolder == -1):
            return -1
        else:
            BotonesFolder = self.Data['StreamDeck'][IdFolder]['StreamDeck']
            for tecla in range(len(BotonesFolder)):
                if BotonesFolder[tecla]['Nombre'] == Nombre:
                    return tecla

    def CambiarEstadoBoton(self, IdFolder, IdBoton, Estado):
        self.Data['StreamDeck'][IdFolder]['StreamDeck'][IdBoton]['Estado'] = Estado

    def EsEsena(self, IdFolder, IdEsena):
        if 'OBS' in self.Data['StreamDeck'][IdFolder]['StreamDeck'][IdEsena]:
            if self.Data['StreamDeck'][IdFolder]['StreamDeck'][IdEsena]['OBS'] == "Esena":
                return True
        return False

    def CargarTeclados(self):
        if 'Teclados' in self.Data:
            self.ListaTeclados = []
            for Teclado in self.Data['Teclados']:
                TecladoActual = TecladoMacros.TecladoMacro(Teclado['Nombre'], Teclado['Input'], Teclado['File'])
                if TecladoActual.Conectar():
                    self.ListaTeclados.append(TecladoActual)
            self.ConfigurandoTeclados("")

    def ConfigurandoTeclados(self, Directorio):
        for Teclado in self.ListaTeclados:
            Teclado.ActualizarTeclas(Directorio)
