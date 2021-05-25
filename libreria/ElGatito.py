import logging
import os

import libreria.acciones.MiOBS as MiOBS
import libreria.MiMQTT as MiMQTT

from libreria.MiStreamDeck import IniciarStreamDeck, MiStreamDeck
from libreria.MiDeckImagen import DefinirFuente, DefinirImagenes
from libreria.MiTecladoMacro import MiTecladoMacro
from libreria.FuncionesLogging import ConfigurarLogging
from libreria.FuncionesArchivos import ObtenerArchivo, ObtenerFolder, UnirPath, SalvarArchivo, ObtenerArhivos, ObtenerValor, SalvarValor
from libreria.acciones.Acciones import AccionesExtra
from libreria.acciones.Data_Archivo import AccionDataArchivo
from libreria.acciones.EmularTeclado import ComandoPrecionar


logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


class ElGatito(object):

    def __init__(self, Data):
        self.Data = Data
        self.acciones = dict()
        self.CargarData()
        self.CargarTeclados()
        self.CargarStreamDeck()
        self.IniciarStreamDeck()
        self.IniciarMQTT()
        self.Configurar()

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
                if 'nombre' in Teclado and 'input' in Teclado and 'file' in Teclado:
                    TecladoActual = MiTecladoMacro(Teclado['nombre'], Teclado['input'], Teclado['file'], self.Evento)
                    if TecladoActual.Conectar():
                        self.ListaTeclados.append(TecladoActual)

    def CargarStreamDeck(self):
        """configurando streamdeck"""
        self.ListaDeck = []
        if 'deck' in self.Data:
            logger.info("Cargando StreamDeck")
            CargarDeck = IniciarStreamDeck(self.Data['deck'], self.Evento)
            for Deck in CargarDeck:
                DeckActual = MiStreamDeck(Deck)
                self.ListaDeck.append(DeckActual)
            if 'fuente' in self.Data:
                DefinirFuente(self.Data['fuente'])
                DefinirImagenes(self.Data['imagenes'])

    def ActualizarDeck(self):
        for Deck in self.ListaDeck:
            if 'streamdeck' in self.acciones:
                Deck.ActualizarIconos(self.acciones['streamdeck'], self.desfaceDeck, True)
            elif Deck.Nombre in self.acciones:
                Deck.ActualizarIconos(self.acciones[Deck.Nombre], self.desfaceDeck)

    def LimpiarDeck(self):
        for Deck in self.ListaDeck:
            if 'streamdeck' in self.acciones:
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
        if 'streamdeck' in self.acciones:
            self.desfaceDeck = 0
            # TODO Error cuando no entra a streamdeck

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
                        if Evento['estado']:
                            logger.info(f"Evento {NombreEvento}[{accion['key']}] {accion['nombre']}")
                        self.EjecutandoEvento(accion, Evento['estado'])
                        return

        if 'deck' in Evento:
            if 'streamdeck' in self.acciones:
                key_desface = Evento['key'] + Evento['base'] + self.desfaceDeck
                for accion in self.acciones['streamdeck']:
                    if 'key' in accion:
                        if accion['key'] == key_desface:
                            if Evento['estado']:
                                logger.info(f"Evento streamdeck[{accion['key']}] {accion['nombre']}")
                            self.EjecutandoEvento(accion, Evento['estado'])
                            return
                logger.info(f"Evento no asignado streamdeck[{key_desface}]")
                return
            else:
                pass

        logger.info(f"Evento no asignado {NombreEvento}[{Evento['key']}]")

    def EjecutandoEvento(self, accion, estado):
        if estado:
            if 'macro' in accion:
                for Comando in accion['macro']:
                    self.EjecutandoEvento(Comando, estado)
            if 'opcion' in accion:
                self.AccionesOpcion(accion)
            elif 'deck' in accion:
                self.AccionesDeck(accion)
            elif 'obs' in accion:
                self.AccionesOBS(accion)
            elif 'data_archivo' in accion:
                AccionDataArchivo(accion)
            elif 'tecla_on' in accion:
                ComandoPrecionar(accion['tecla_on'], estado)
            else:
                AccionesExtra(accion)
        else:
            if 'tecla_off' in accion:
                ComandoPrecionar(accion['tecla_off'], estado)
            elif 'tecla_on' in accion:
                ComandoPrecionar(accion['tecla_on'], estado)

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
        elif Opcion == 'actualizar':
            self.ActualizarDeck()
        else:
            logger.warning(f"Opcion No Encontrada: {Opcion}")

    def AccionesDeck(self, accion):
        opcion = accion['deck']
        if opcion == "brillo":
            Brillo = ObtenerValor("data/streamdeck.json", "brillo")
            Brillo += accion['cantidad']
            if Brillo < 0:
                Brillo = 0
                return
            elif Brillo > 100:
                Brillo = 100
                return
            logger.info(F"Asignando brillo {Brillo} a Decks")
            SalvarValor("data/streamdeck.json", "brillo", Brillo)
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
        elif opcion == 'filtro':
            if self.OBS is not None:
                self.OBS.CambiarFiltro(accion['fuente'], accion['filtro'], not accion['estado'])
        elif opcion == 'fuente':
            if self.OBS is not None:
                self.OBS.CambiarFuente(accion['fuente'], not accion['estado'])
        elif opcion == 'grabando':
            if self.OBS is not None:
                self.OBS.CambiarGrabacion()
        elif opcion == 'envivo':
            if self.OBS is not None:
                self.OBS.CambiarEnVivo()

    def MoverPagina(self, Direcion):
        if 'streamdeck' in self.acciones:
            UltimoDeck = self.ListaDeck[-1]
            Cantidad = UltimoDeck.Base + UltimoDeck.Cantidad
            UltimaAccion = self.acciones['streamdeck'][-1]
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

    def IniciarStreamDeck(self):
        self.PathActual = "defaul"
        self.BuscarFolder(self.PathActual)
        self.ActualizarDeck()

    def IniciarMQTT(self):
        if 'broker_mqtt' in self.Data:
            self.MQTT = MiMQTT.MiMQTT(self.Data['broker_mqtt'])
        else:
            self.MQTT = MiMQTT.MiMQTT()
        self.MQTT.Conectar()

    def Configurar(self):
        SalvarArchivo("data/obs.json", dict())
        SalvarArchivo("data/fuente_obs.json", dict())
        SalvarArchivo("data/filtro_obs.json", dict())
        self.OBS = None
