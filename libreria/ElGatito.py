import os


from .MiDeck.MiStreamDeck import IniciarStreamDeck, MiStreamDeck2
from .MiDeck.MiDeckImagen import DefinirImagenes
from .MiDeck.MiDeckExtras import DefinirFuente

from .acciones.Acciones import AccionesExtra
from .acciones.Data_Archivo import AccionDataArchivo
from .acciones.EmularTeclado import ComandoPrecionar
from .acciones.MiOBS import MiOBS
from .MiMQTT import MiMQTT
from .MiTecladoMacro import MiTecladoMacro

from acciones import CargarAcciones

from MiLibrerias import ConfigurarLogging
from MiLibrerias import UnirPath, RelativoAbsoluto, ObtenerListaFolder, ObtenerListaArhivos
from MiLibrerias import SalvarValor, ObtenerValor, ObtenerArchivo

logger = ConfigurarLogging(__name__)


class ElGatito(object):
    """Clase base de Sistema de Macro ElGatoALSW."""

    def __init__(self):

        self.Data = ObtenerArchivo('config.json')
        if self.Data is None:
            logger.error("No existe archivo config.json")
            os._exit(0)
        self.acciones = dict()

        self.CargarOBS()
        self.IniciarAcciones()
        self.CargarData()
        self.CargarStreamDeck()
        self.CargarTeclados()
        self.IniciarStreamDeck()
        # self.IniciarMQTT()

    def IniciarAcciones(self):
        """
            Inicializa las acciones del Sistema en dict nombre de la accion y la funcion asociada
        """
        logger.info("Cargando Acciones")
        ListaAcciones = CargarAcciones()

        # Acciones Macro
        ListaAcciones['macro'] = self.AccionesMacros

        # Acciones Sistema
        ListaAcciones['salir'] = self.Salir
        ListaAcciones['reiniciar_data'] = self.Reiniciar
        ListaAcciones['entrar_folder'] = self.Entrar_Folder
        ListaAcciones['regresar_folder'] = self.Regresar_Folder
        ListaAcciones['actualizar_folder'] = self.Actualizar_Folder
        ListaAcciones['siquiente_pagina'] = self.Siquiente_Pagina
        ListaAcciones['anterior_pagina'] = self.Anterior_Pagina

        # Acciones OBS
        ListaAcciones['obs_conectar'] = self.OBS.Conectar
        ListaAcciones['obs_host'] = self.OBS.Conectar
        ListaAcciones['obs_grabar'] = self.OBS.CambiarGrabacion
        ListaAcciones['obs_envivo'] = self.OBS.CambiarEnVivo
        ListaAcciones['obs_esena'] = self.OBS.CambiarEsena
        ListaAcciones['obs_fuente'] = self.OBS.CambiarFuente
        ListaAcciones['obs_filtro'] = self.OBS.CambiarFiltro
        ListaAcciones['obs_server'] = self.OBS.Conectar

        # Acciones Deck
        ListaAcciones['deck_brillo'] = self.DeckBrillo

        self.ListaAcciones = ListaAcciones

    def CargarData(self):
        """Cargando Data para Dispisitivo."""
        logger.info("Cargando Data")
        if 'deck_file' in self.Data:
            self.Data['deck'] = ObtenerArchivo(
                self.Data['deck_file'])
            if self.Data['deck'] is None:
                logger.error(
                    f"Archivo de config de Strean Deck[{self.Data['teclados_file']}] no exste")
                self.Data.pop('deck')

        if 'teclados_file' in self.Data:
            self.Data['teclados'] = ObtenerArchivo(
                self.Data['teclados_file'])
            if self.Data['teclados'] is None:
                logger.error(
                    f"Archivo de config de Teclado[{self.Data['teclados_file']}] no exste")
                self.Data.pop('teclados')

        if 'folder_path' in self.Data:
            self.PathActual = self.Data['folder_path']
            self.Keys = {"nombre": self.Data['folder_path'],
                         "folder_path": self.Data['folder_path']}
            self.CargarFolder(self.Keys)

    def CargarFolder(self, Data):
        ListaFolder = ObtenerListaFolder(Data['folder_path'])
        ListaArchivos = ObtenerListaArhivos(Data['folder_path'])

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
        """Confiurando Teclados Macros."""
        self.ListaTeclados = []
        if 'teclados' in self.Data:
            logger.info("Cargando Teclados")
            for Teclado in self.Data['teclados']:
                if 'nombre' in Teclado and 'input' in Teclado and 'file' in Teclado:
                    TecladoActual = MiTecladoMacro(
                        Teclado['nombre'], Teclado['input'], Teclado['file'], self.Evento)
                    TecladoActual.Conectar()
                    self.ListaTeclados.append(TecladoActual)

    def CargarStreamDeck(self):
        """Configurando streamdeck."""
        self.ListaDeck = []
        if 'fuente' in self.Data:
            DefinirFuente(self.Data['fuente'])
            DefinirImagenes(self.Data['imagenes'])
        if 'deck' in self.Data:
            logger.info("Cargando StreamDeck2")
            Cantidad_Base = 0
            for InfoDeck in self.Data['deck']:
                DeckActual = MiStreamDeck2(
                    InfoDeck, self.Evento, Cantidad_Base)
                DeckActual.Conectar()
                Cantidad_Base += DeckActual.Cantidad
                self.ListaDeck.append(DeckActual)
            self.ListaDeck.sort(key=lambda x: x.ID, reverse=False)
            #     self.ListaDeck.append(DeckActual)
            # CargarDeck = IniciarStreamDeck(self.Data['deck'], self.Evento)
            # for Deck in CargarDeck:
            #     DeckActual = MiStreamDeck(Deck)

    def ActualizarDeck(self):
        for Deck in self.ListaDeck:
            if 'streamdeck' in self.acciones:
                Deck.CambiarFolder(self.PathActual)
                Deck.ActualizarIconos(
                    self.acciones['streamdeck'], self.desfaceDeck, Unido=True)

            elif Deck.Nombre in self.acciones:
                Deck.CambiarFolder(self.PathActual)
                Deck.ActualizarIconos(
                    self.acciones[Deck.Nombre], self.desfaceDeck)

    def ActualizarDeckIcono(self):

        # TODO: Problemar cuando funcion se llama muchas veces el gifs empieza a fallar
        for Deck in self.ListaDeck:
            if 'streamdeck' in self.acciones:
                Deck.ActualizarIconos(
                    self.acciones['streamdeck'], self.desfaceDeck, Unido=True)

            elif Deck.Nombre in self.acciones:
                Deck.ActualizarIconos(
                    self.acciones[Deck.Nombre], self.desfaceDeck)

    def LimpiarDeck(self):
        for Deck in self.ListaDeck:
            if 'streamdeck' in self.acciones:
                Deck.Limpiar()
            elif Deck.Nombre in self.acciones:
                Deck.Limpiar()

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
                logger.info(
                    f"Encontro Config {Atributo} de {nombreDispositivo}")
                self.acciones[nombreDispositivo] = Data[nombreDispositivo]

    def BuscarDentroFolder(self, Folderes, Data):
        if 'nombre' in Data:
            if Data['nombre'] == Folderes[0]:
                Folderes.remove(Data['nombre'])
                if len(Folderes) > 0:
                    if 'folder' in Data:
                        for BuscarFolder in Data['folder']:
                            Data = self.BuscarDentroFolder(
                                Folderes, BuscarFolder)
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
                            logger.info(
                                f"Evento {NombreEvento}[{accion['key']}] {accion['nombre']}")
                        self.EjecutandoEvento(accion, Evento['estado'])
                        return

        if 'deck' in Evento:
            if 'streamdeck' in self.acciones:
                key_desface = Evento['key'] + Evento['base'] + self.desfaceDeck
                for accion in self.acciones['streamdeck']:
                    if 'key' in accion:
                        if accion['key'] == key_desface:
                            # if Evento['estado']:
                            # logger.info(
                            # f"Evento streamdeck[{accion['key']}] {accion['nombre']}")
                            self.EjecutandoEvento(accion, Evento['estado'])
                            return
                logger.info(f"Evento no asignado streamdeck[{key_desface}]")
                return
            else:
                pass

        logger.info(f"Evento no asignado {NombreEvento}[{Evento['key']}]")

    def EjecutandoEvento(self, accion, estado):
        if estado:
            if 'accion' in accion:
                accion['precionado'] = estado
                # TODO: Ver como pasar estado entre macros
                self.BuscarAccion(accion)

            elif 'macro' in accion:
                for Comando in accion['macro']:
                    self.EjecutandoEvento(Comando, estado)
            elif 'opcion' in accion:
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
                AccionesExtra(accion, self.PathActual)
        else:
            if 'tecla_off' in accion:
                ComandoPrecionar(accion['tecla_off'], estado)
            elif 'tecla_on' in accion:
                ComandoPrecionar(accion['tecla_on'], estado)

    def BuscarAccion(self, accion):
        NombreAccion = accion['accion']
        if NombreAccion in self.ListaAcciones:
            if 'nombre' in accion:
                Nombre = accion['nombre']
                logger.info(f"Accion[{NombreAccion}] - {Nombre}")
            else:
                logger.info(f"Accion[{NombreAccion}]")
            if 'opciones' in accion:
                OpcionesAccion = accion['opciones']
            else:
                OpcionesAccion = {}
            return self.ListaAcciones[NombreAccion](OpcionesAccion)
        else:
            logger.info(f"No Accion[{NombreAccion}]")
        return None

    def AccionesMacros(self, ListaComando):
        """
            Ejecuta acciones una por una de una lista y si existe data la pasa a la siquiente accion

            ListaComandos -> list
                Acciones a realizar
        """
        respuesta = None
        for Comando in ListaComando:
            if respuesta is not None:
                Opciones = Comando['opciones']
                if 'data_in' in Opciones:
                    DataIn = Opciones['data_in']
                    Opciones[DataIn] = respuesta
            respuesta = self.BuscarAccion(Comando)
    #     ProcesoAccion = multiprocessing.Process(target=self.HacerMacro, args=[ListaComando])
    #     ProcesoAccion.start()

    # def HacerMacro(self, ListaComando):
    #     respuesta = None
    #     for Comando in ListaComando:
    #         if respuesta is not None:
    #             Opciones = Comando['opciones']
    #             if 'data_in' in Opciones:
    #                 DataIn = Opciones['data_in']
    #                 Opciones[DataIn] = respuesta
    #         respuesta = self.BuscarAccion(Comando)

    def Reiniciar(self, Opciones):
        """
            Reinicia la data del programa.
        """
        logger.info("Reiniciar data ElGatoALSW")
        self.ReiniciarData()

    def Regresar_Folder(self, Opciones):
        Direcion = self.PathActual.split("/")
        self.PathActual = "/".join(Direcion[:-1])
        if self.PathActual == "":
            self.PathActual = "defaul"
            return
        logger.info(f"Regresar[{self.PathActual}]")
        self.BuscarFolder(self.PathActual)
        self.LimpiarDeck()
        self.ActualizarDeck()

    def Entrar_Folder(self, opciones):
        if 'folder' in opciones:
            Folder = opciones['folder']
        else:
            return
        logger.info(f"Entrando[{Folder}]")
        self.PathActual = RelativoAbsoluto(Folder, self.PathActual)
        self.BuscarFolder(self.PathActual)
        self.LimpiarDeck()
        self.ActualizarDeck()

    def Actualizar_Folder(self, Opciones):
        self.ActualizarDeck()

    def Siquiente_Pagina(self, Opciones):
        self.MoverPagina('siquiente')

    def Anterior_Pagina(self, Opciones):
        self.MoverPagina('anterior')

    def AccionesOpcion(self, accion):
        Opcion = accion['opcion']
        if Opcion == "salir":
            logger.info("Saliendo ElGatoALSW - Adios :) ")
            self.LimpiarDeck()
            os._exit(0)
        elif Opcion == 'recargar':
            pass
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
            self.PathActual = RelativoAbsoluto(accion['path'], self.PathActual)
            self.BuscarFolder(self.PathActual)
            self.LimpiarDeck()
            self.ActualizarDeck()
        elif Opcion == 'actualizar':
            self.ActualizarDeck()
        else:
            logger.warning(f"Opcion No Encontrada: {Opcion}")

    def DeckBrillo(self, Opciones):
        Brillo = ObtenerValor("data/streamdeck.json", "brillo")
        def constrain(n, minn, maxn): return max(min(maxn, n), minn)
        if 'cantidad' in Opciones:
            cantidad = Opciones['cantidad']
        else:
            return
        Brillo += cantidad
        Brillo = constrain(Brillo, 0, 100)
        logger.info(F"Deck[Brillo]: {Brillo}")
        SalvarValor("data/streamdeck.json", "brillo", Brillo)
        for deck in self.ListaDeck:
            deck.Brillo(Brillo)

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
        elif opcion == "reiniciar":
            logger.info("Reiniciar todo el Sistema ElGatoALSW")
            self.Reiniciar()

    def AccionesOBS(self, accion):
        """Acciones para controlar OBS Websocket."""
        opcion = accion['obs']
        if opcion == 'conectar':
            self.OBS.Reiniciar()
            # self.OBS.DibujarDeck(self.ActualizarDeckIcono)
            self.OBS.Conectar()
        elif opcion == 'server':
            self.OBS.Reiniciar()
            self.OBS.CambiarHost(accion['server'])
            # self.OBS.DibujarDeck(self.ActualizarDeckIcono)
            self.OBS.Conectar()
        elif opcion == 'cerrar':
            self.OBS.Desconectar()
        elif self.OBS.Conectado:
            if opcion == 'esena':
                self.OBS.CambiarEsena(accion['esena'])
            elif opcion == 'fuente':
                self.OBS.CambiarFuente(accion['fuente'])
            elif opcion == 'filtro':
                Filtro = [accion['fuente'], accion['filtro']]
                self.OBS.CambiarFiltro(Filtro)
            elif opcion == 'grabando':
                self.OBS.CambiarGrabacion()
            elif opcion == 'envivo':
                self.OBS.CambiarEnVivo()
            else:
                logger.warning("Opcion no encontrada")
        else:
            logger.warning("OBS Websocket no conectado")

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
        self.LimpiarDeck()
        self.ActualizarDeck()

    def IniciarMQTT(self):
        """Iniciar coneccion con Broker MQTT."""
        if 'broker_mqtt' in self.Data:
            self.MQTT = MiMQTT(self.Data['broker_mqtt'])
        else:
            self.MQTT = MiMQTT()
        self.MQTT.Conectar()

    def ReiniciarData(self):
        """
            Reinicia data de los Botones Actuales.
        """
        self.Data = ObtenerArchivo('config.json')
        self.acciones = dict()
        self.CargarData()
        self.IniciarStreamDeck()

    def CargarOBS(self):
        """
            Inicialioza el Objeto de OBS
        """
        self.OBS = MiOBS()
        self.OBS.DibujarDeck(self.ActualizarDeckIcono)

    def __exit__(self, exc_type, exc_value, traceback):
        print("Hora de matar todo XD")
        # for file in self.files:
        #     os.unlink(file)

    def __del__(self):
        print("I'm being automatically destroyed. Goodbye!")

    def Salir(self, Opciones):
        """
            Cierra el programa.
        """
        logger.info("Saliendo ElGatoALSW - Adios :) ")
        self.OBS.Desconectar()
        # self.MQTT.Desconectar()
        for Teclado in self.ListaTeclados:
            Teclado.Desconectar()
        for deck in self.ListaDeck:
            deck.Desconectar()
        # self.LimpiarDeck()
        # raise SystemExit
        os._exit(0)
