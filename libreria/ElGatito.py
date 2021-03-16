import logging
import os

import libreria.acciones.MiOBS as MiOBS

from libreria.MiStreanDeck import IniciarStreanDeck, MiStreanDeck
from libreria.MiDeckImagen import DefinirFuente, DefinirImagenes
from libreria.MiTecladoMacro import MiTecladoMacro
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import ObtenerArchivo, ObtenerFolder, UnirPath, SalvarArchivo, ObtenerArhivos, ObtenerValor, SalvarValor
from libreria.FuncionesHilos import CargarHilo
from libreria.acciones.Acciones import AccionesExtra


logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class ElGatito(object):

    def __init__(self, Data):
        self.Data = Data
        self.acciones = dict()
        self.CargarData()
        self.CargarTeclados()
        self.CargarStreanDeck()
        self.IniciarStreanDeck()
        self.Configurar()
        CargarHilo()

    def CargarData(self):
        """Cargando Data para Dispisitivo"""
        logger.info("Cargando Data")
        if 'deck_file' in self.Data:
            self.Data['deck'] = ObtenerArchivo(self.Data['deck_file'])

        if 'teclados_file' in self.Data:
            self.Data['teclados'] = ObtenerArchivo(self.Data['teclados_file'])

        if 'folder_path' in self.Data:
            self.PathActual = self.Data['folder_path']
            self.Keys = {"nombre": self.Data['folder_path'],
                         "folder_path": self.Data['folder_path']}
            self.CargarFolder(self.Keys)

    def CargarFolder(self, Data):
        ListaFolder = ObtenerFolder(Data['folder_path'])
        ListaArchivos = ObtenerArhivos(Data['folder_path'])

        if len(ListaArchivos) > 0:
            for Archivo in ListaArchivos:
                self.CargarArchivos('teclados', Data, Archivo)
                self.CargarArchivos('global', Data, Archivo)
                self.CargarArchivos('deck', Data, Archivo)

        if len(ListaFolder) > 0:
            Data["folder"] = []
            for Folder in ListaFolder:
                pathActual = UnirPath(Data['folder_path'], Folder)
                data = {"nombre": Folder,
                        "folder_path": pathActual}
                Data["folder"].append(data)
            if "folder" in Data:
                for Folder in Data["folder"]:
                    self.CargarFolder(Folder)

    def CargarArchivos(self, Atributo, Data, Archivo):
        if Atributo in self.Data:
            for ArchivosTeclado in self.Data[Atributo]:
                if ArchivosTeclado['file'] == Archivo:
                    path = UnirPath(Data['folder_path'], Archivo)
                    DataArchivo = ObtenerArchivo(path)
                    DataAtributo = ArchivosTeclado['nombre']
                    Data[DataAtributo] = DataArchivo

    def CargarTeclados(self):
        """Confiurando Teclados Macros"""
        if 'teclados' in self.Data:
            logger.info("Cargando Teclados")
            self.ListaTeclados = []
            for Teclado in self.Data['teclados']:
                TecladoActual = MiTecladoMacro(Teclado['nombre'], Teclado['input'], Teclado['file'], self.Evento)
                if TecladoActual.Conectar():
                    self.ListaTeclados.append(TecladoActual)

    def CargarStreanDeck(self):
        """configurando StreanDeck"""
        self.ListaDeck = []
        if 'deck' in self.Data:
            logger.info("Cargando StreamDeck")
            CargarDeck = IniciarStreanDeck(self.Data['deck'], self.Evento)
            for Deck in CargarDeck:
                DeckActual = MiStreanDeck(Deck)
                self.ListaDeck.append(DeckActual)
            if 'fuente' in self.Data:
                DefinirFuente(self.Data['fuente'])
                DefinirImagenes(self.Data['imagenes'])

    def ActualizarDeck(self):
        for Deck in self.ListaDeck:
            if 'streandeck' in self.acciones:
                Deck.ActualizarIconos(self.acciones['streandeck'], self.desfaceDeck, True)
            elif Deck.Nombre in self.acciones:
                Deck.ActualizarIconos(self.acciones[Deck.Nombre], self.desfaceDeck)

    def LimpiarDeck(self):
        for Deck in self.ListaDeck:
            if 'streandeck' in self.acciones:
                Deck.Limpiar()
            elif Deck.Nombre in self.acciones:
                Deck.Limpiar()

    def ConfigurandoTeclados(self, Directorio):
        for Teclado in self.ListaTeclados:
            Teclado.ActualizarTeclas(Directorio)

    def BuscarFolder(self, Folder):
        Data = self.Keys
        Folderes = Folder.split('/')
        if len(Folderes) > 0:
            Data = self.BuscarDentroFolder(Folderes, Data)
            if Data is not None:
                # SalvarArchivo("Data.json", Data)
                self.CargarAcciones('teclados', Data)
                self.CargarAcciones('global', Data)
                self.CargarAcciones('deck', Data)
        if 'streandeck' in self.acciones:
            self.desfaceDeck = 0
            # TODO Error cuando no entra a streandeck

    def CargarAcciones(self, Atributo, Data):
        for dispositivo in self.Data[Atributo]:
            nombreDispositivo = dispositivo['nombre']
            if nombreDispositivo in Data:
                logger.info(f"Encontro Config {Atributo} de {nombreDispositivo}")
                self.acciones[nombreDispositivo] = Data[nombreDispositivo]

    def BuscarDentroFolder(self, Folderes, Data):
        if 'nombre' in Data:
            if Data['nombre'] == Folderes[0]:
                Folderes.remove(Data['nombre'])
                if len(Folderes) > 0:
                    if 'folder' in Data:
                        for BuscarFolder in Data['folder']:
                            Data = self.BuscarDentroFolder(Folderes, BuscarFolder)
                            if Data is not None:
                                return Data
                else:
                    return Data

    def Evento(self, Evento):
        NombreEvento = Evento['nombre']
        if NombreEvento in self.acciones:
            for accion in self.acciones[NombreEvento]:
                if 'key' in accion:
                    if accion['key'] == Evento['key']:
                        logger.info(f"Evento {NombreEvento}[{accion['key']}] {accion['nombre']}")
                        self.EjecutandoEvento(accion)
                        return

        if 'deck' in Evento:
            if 'streandeck' in self.acciones:
                key_desface = Evento['key'] + Evento['base'] + self.desfaceDeck
                for accion in self.acciones['streandeck']:
                    if 'key' in accion:
                        if accion['key'] == key_desface:
                            logger.info(f"Evento StreanDeck[{accion['key']}] {accion['nombre']}")
                            self.EjecutandoEvento(accion)
                            return
                logger.info(f"Evento no asignado StreanDeck[{key_desface}]")
                return
            else:
                pass

        logger.info(f"Evento no asignado {NombreEvento}[{Evento['key']}]")

    def EjecutandoEvento(self, accion):
        if 'opcion' in accion:
            self.AccionesOpcion(accion)
        elif 'deck' in accion:
            self.AccionesDeck(accion)
        elif 'obs' in accion:
            self.AccionesOBS(accion)
        else:
            AccionesExtra(accion)

    def AccionesOpcion(self, accion):
        Opcion = accion['opcion']
        if Opcion == "salir":
            logger.info("Saliendo ElGatoALSW - Adios :) ")
            os._exit(0)
        elif Opcion == 'siquiente':
            self.MoverPagina('siquiente')
        elif Opcion == 'anterior':
            self.MoverPagina('anterior')
        elif Opcion == 'regresar':
            Direcion = self.PathActual.split("/")
            self.PathActual = "/".join(Direcion[:-1])
            if self.PathActual == "":
                self.PathActual = "defaul"
                return
            logger.info(f"Regresar Folder {self.PathActual}")
            self.BuscarFolder(self.PathActual)
            self.LimpiarDeck()
            self.ActualizarDeck()
        elif Opcion == 'folder':
            logger.info(f"Entrando a {accion['path']}")
            self.PathActual = accion['path']
            self.BuscarFolder(self.PathActual)
            self.LimpiarDeck()
            self.ActualizarDeck()
        else:
            logger.warning(f"Opcion No Encontrada: {Opcion}")

    def AccionesDeck(self, accion):
        opcion = accion['deck']
        if opcion == "brillo":
            Brillo = ObtenerValor("data/streandeck.json", "brillo")
            Brillo += accion['cantidad']
            if Brillo < 0:
                Brillo = 0
                return
            elif Brillo > 100:
                Brillo = 100
                return
            logger.info(F"Asignando brillo {Brillo} a Decks")
            SalvarValor("data/streandeck.json", "brillo", Brillo)
            for deck in self.ListaDeck:
                deck.Brillo(Brillo)

    def AccionesOBS(self, accion):
        opcion = accion['obs']
        if opcion == 'conectar':
            self.OBS = MiOBS.MiOBS()
            self.OBS.DibujarDeck(self.ActualizarDeck)
            self.OBS.Conectar()
        elif opcion == 'server':
            self.OBS = MiOBS.MiOBS()
            self.OBS.CambiarHost(accion['server'])
            self.OBS.DibujarDeck(self.ActualizarDeck)
            self.OBS.Conectar()
        elif opcion == 'cerrar':
            self.OBS.Desconectar()
        elif opcion == 'esena':
            if self.OBS is not None:
                self.OBS.CambiarEsena(accion['esena'])
        elif opcion == 'grabando':
            if self.OBS is not None:
                self.OBS.CambiarGrabacion()
        elif opcion == 'envivo':
            if self.OBS is not None:
                self.OBS.CambiarEnVivo()

    def MoverPagina(self, Direcion):
        if 'streandeck' in self.acciones:
            UltimoDeck = self.ListaDeck[-1]
            Cantidad = UltimoDeck.Base + UltimoDeck.Cantidad
            UltimaAccion = self.acciones['streandeck'][-1]
            if Direcion == 'siquiente':
                self.desfaceDeck += Cantidad
                if self.desfaceDeck >= UltimaAccion['key']:
                    self.desfaceDeck -= Cantidad
                    return
                logger.info("Siquiente Pagina")
            elif Direcion == 'anterior':
                self.desfaceDeck -= Cantidad
                if self.desfaceDeck < 0:
                    self.desfaceDeck = 0
                    return
                logger.info("Anterior Pagina")
            self.LimpiarDeck()
            self.ActualizarDeck()
        else:
            pass

    def IniciarStreanDeck(self):
        self.PathActual = "defaul"
        self.BuscarFolder(self.PathActual)
        self.ActualizarDeck()

    def Configurar(self):
        SalvarArchivo("data/obs.json", dict())
        self.OBS = None
