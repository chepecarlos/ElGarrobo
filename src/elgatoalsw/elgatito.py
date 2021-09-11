import os

# from .MiMQTT import MiMQTT
# from .acciones.Acciones import AccionesExtra
# from .acciones.Data_Archivo import AccionDataArchivo
# from .acciones.EmularTeclado import ComandoPrecionar
# from .acciones.MiOBS import MiOBS

# from .MiTecladoMacro import MiTecladoMacro

from extras.mi_obs import MiOBS

from dispositivos.miteclado.mi_teclado_macro import MiTecladoMacro
from dispositivos.mideck.mi_streamdeck import MiStreamDeck
from dispositivos.mideck.mi_deck_extra import DefinirFuente
from dispositivos.mideck.mi_deck_imagen import DefinirImagenes
from dispositivos.mimqtt.mi_mqtt import MiMQTT


from acciones import CargarAcciones

from MiLibrerias import ConfigurarLogging
from MiLibrerias import UnirPath, RelativoAbsoluto, ObtenerListaFolder, ObtenerListaArhivos
from MiLibrerias import SalvarValor, ObtenerValor, ObtenerArchivo

logger = ConfigurarLogging(__name__)


class ElGatito(object):
    """Clase base de Sistema de Macro ElGatoALSW."""

    def __init__(self):

        logger.info(f"Configurando[config.json]")

        self.Data = ObtenerArchivo('config.json')
        if self.Data is None:
            logger.error("No existe archivo config.json")
            os._exit(0)

        self.acciones = dict()

        self.IniciarModulo()

        self.CargarData()

        if self.ModuloOBS:
            self.CargarOBS()

        if self.ModuloDeck:
            self.CargarStreamDeck()
            self.IniciarStreamDeck()

        if self.ModuloTeclado:
            self.CargarTeclados()

        if self.ModuloMQTT:
            self.IniciarMQTT()

        self.IniciarAcciones()

    def IniciarModulo(self):
        """
            Carga los modulos activos.
        """
        logger.info(f"Configurando[Modulos]")
        Modulos = ObtenerArchivo('modulos.json')

        self.ModuloOBS = False
        self.ModuloDeck = False
        self.ModuloTeclado = False
        self.ModuloMQTT = False

        if 'obs' in Modulos:
            self.ModuloOBS = Modulos['obs']

        if 'deck' in Modulos:
            self.ModuloDeck = Modulos['deck']

        if 'teclado' in Modulos:
            self.ModuloTeclado = Modulos['teclado']

        if 'mqtt' in Modulos:
            self.ModuloMQTT = Modulos['mqtt']

    def IniciarAcciones(self):
        """
            Inicializa las acciones del Sistema en dict nombre de la accion y la funcion asociada
        """
        logger.info("Acciones[Cargando]")
        ListaAcciones = CargarAcciones()

        # Acciones Macro
        ListaAcciones['macro'] = self.AccionesMacros

        # Acciones Sistema
        ListaAcciones['salir'] = self.Salir
        ListaAcciones['reiniciar_data'] = self.Reiniciar
        ListaAcciones['entrar_folder'] = self.Entrar_Folder
        ListaAcciones['regresar_folder'] = self.Regresar_Folder

        # Acciones Deck
        if self.ModuloDeck:
            ListaAcciones['siquiente_pagina'] = self.Siquiente_Pagina
            ListaAcciones['anterior_pagina'] = self.Anterior_Pagina
            ListaAcciones['actualizar_pagina'] = self.Actualizar_Folder
            ListaAcciones['deck_brillo'] = self.DeckBrillo

        # Acciones OBS
        if self.ModuloOBS:
            ListaAcciones['obs_conectar'] = self.OBS.Conectar
            ListaAcciones['obs_desconectar'] = self.OBS.Desconectar
            ListaAcciones['obs_grabar'] = self.OBS.CambiarGrabacion
            ListaAcciones['obs_envivo'] = self.OBS.CambiarEnVivo
            ListaAcciones['obs_escena'] = self.OBS.CambiarEscena
            ListaAcciones['obs_fuente'] = self.OBS.CambiarFuente
            ListaAcciones['obs_filtro'] = self.OBS.CambiarFiltro
            # ListaAcciones['obs_host'] = self.OBS.Conectar
            # ListaAcciones['obs_server'] = self.OBS.Conectar

        self.ListaAcciones = ListaAcciones

    def CargarData(self):
        """
            Cargando Data para Dispisitivo.
        """
        logger.info("Cargando[Eventos]")
        if self.ModuloDeck:
            if 'deck_file' in self.Data:
                self.Data['deck'] = ObtenerArchivo(
                    self.Data['deck_file'])
                if self.Data['deck'] is None:
                    logger.error(
                        f"Archivo de config de Strean Deck[{self.Data['teclados_file']}] no exste")
                    self.Data.pop('deck')

        if self.ModuloTeclado:
            if 'teclados_file' in self.Data:
                ArchivoTeclado = self.Data['teclados_file']
                self.Data['teclados'] = ObtenerArchivo(ArchivoTeclado)
                if self.Data['teclados'] is None:
                    logger.error(
                        f"Archivo de config de Teclado[{ArchivoTeclado}] no exste")
                    self.Data.pop('teclados')

        if 'folder_path' in self.Data:
            self.PathActual = self.Data['folder_path']
            self.Keys = {"nombre": self.Data['folder_path'],
                         "folder_path": self.Data['folder_path']}
            self.CargarFolder(self.Keys)

        if self.ModuloMQTT:
            if 'mqtt_file' in self.Data:
                ArchivoMQTT = self.Data['mqtt_file']
                self.Data['mqtt'] = ObtenerArchivo(ArchivoMQTT)
                if self.Data['mqtt'] is None:
                    logger.error(
                        f"Archivo de config de Teclado[{ArchivoMQTT}] no exste")
                    self.Data.pop('mqtt')

    def CargarFolder(self, Data):
        """
            Carga recursivamente las configuracion de los diferentes eventos por dispositivos.
        """
        ListaFolder = ObtenerListaFolder(Data['folder_path'])
        ListaArchivos = ObtenerListaArhivos(Data['folder_path'])

        if len(ListaArchivos) > 0:
            for Archivo in ListaArchivos:
                if self.ModuloTeclado:
                    self.CargarArchivos('teclados', Data, Archivo)
                if self.ModuloDeck:
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

    def CargarArchivos(self, Dispositivo, Data, Archivo):
        """
            Carga la informacion de un dispositivo
        """
        if Dispositivo in self.Data:
            for ArchivoDispositivo in self.Data[Dispositivo]:
                if ArchivoDispositivo['file'] == Archivo:
                    Ruta = UnirPath(Data['folder_path'], Archivo)
                    Info = ObtenerArchivo(Ruta)
                    Atributo = ArchivoDispositivo['nombre']
                    Data[Atributo] = Info

    def CargarTeclados(self):
        """
            Confiurando Teclados Macros.
        """
        self.ListaTeclados = []
        if 'teclados' in self.Data:
            logger.info("Teclados[Cargando]")
            for Teclado in self.Data['teclados']:
                if 'nombre' in Teclado and 'input' in Teclado and 'file' in Teclado:
                    TecladoActual = MiTecladoMacro(
                        Teclado['nombre'], Teclado['input'], Teclado['file'], self.Evento)
                    TecladoActual.Conectar()
                    self.ListaTeclados.append(TecladoActual)

    def CargarStreamDeck(self):
        """Configurando streamdeck."""
        if 'fuente' in self.Data:
            DefinirFuente(self.Data['fuente'])
            DefinirImagenes(self.Data['imagenes'])
        if 'deck' in self.Data:
            logger.info("StreamDeck[Cargando]")
            Cantidad_Base = 0
            self.ListaDeck = []
            for InfoDeck in self.Data['deck']:
                DeckActual = MiStreamDeck(
                    InfoDeck, self.Evento, Cantidad_Base)
                DeckActual.Conectar()
                Cantidad_Base += DeckActual.Cantidad
                self.ListaDeck.append(DeckActual)
            self.ListaDeck.sort(key=lambda x: x.ID, reverse=False)
            #     self.ListaDeck.append(DeckActual)
            # CargarDeck = IniciarStreamDeck(self.Data['deck'], self.Evento)
            # for Deck in CargarDeck:
            #     DeckActual = MiStreamDeck(Deck)
        else:
            self.ListaDeck = None

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
        if self.ListaDeck is not None:
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
                logger.info(f"Folder[Configurado] {nombreDispositivo}")
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
                            self.EjecutandoEvento(accion, Evento['estado'])
                            return
                logger.info(f"Evento[No asignado] streamdeck[{key_desface}]")
                return
            else:
                pass
        else:
            pass

        logger.info(f"Evento[No asignado] {NombreEvento}[{Evento['key']}]")

    def EjecutandoEvento(self, evento, estado):
        if estado:
            if 'accion' in evento:
                evento['precionado'] = estado
                # TODO: Ver como pasar estado entre macros
                self.BuscarAccion(evento)
            else:
                logger.info("Evento[no accion]")

    def BuscarAccion(self, accion):
        if 'accion' in accion:
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
                logger.info(f"Accion[No Encontrada] {NombreAccion}")
        else:
            logger.info(f"Accion[No Atributo]")

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

        # TODO: Hacer Macros en diferentes Hilos
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
        """
            Entra en folder

            folder -> str
                folder a entrar
        """
        if 'folder' in opciones:
            Folder = opciones['folder']
        else:
            logger.warning(f"Folder[no encontrado]")
            return
        logger.info(f"Folder[{Folder}]")
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

    def MoverPagina(self, Direcion):
        if 'streamdeck' in self.acciones:
            UltimoDeck = self.ListaDeck[-1]
            Cantidad = UltimoDeck.Base + UltimoDeck.Cantidad
            UltimaAccion = max(
                self.acciones['streamdeck'], key=lambda x: int(x['key'])
            )
            # TODO Limpiar codigo sucio 
            if Direcion == 'siquiente':
                self.desfaceDeck += Cantidad
                if self.desfaceDeck - 1 >= UltimaAccion['key']:
                    self.desfaceDeck -= Cantidad
                    return
                logger.info("Deck[Siquiente Pagina]")
            elif Direcion == 'anterior':
                self.desfaceDeck -= Cantidad
                if self.desfaceDeck < 0:
                    self.desfaceDeck = 0
                    return
                logger.info("Deck[Anterior Pagina]")
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
        for DataMQTT in self.Data['mqtt']:
            self.ListaMQTT = []
            ServidorMQTT = MiMQTT(DataMQTT, self.Evento)
            self.ListaMQTT.append(ServidorMQTT)
        for ServidorMQTT in self.ListaMQTT:
            ServidorMQTT.Conectar()

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
        logger.info("ElGatoALSW[Saliendo] - Adios :) ")
        if self.ModuloOBS:
            self.OBS.Desconectar()
        if self.ModuloTeclado:
            for Teclado in self.ListaTeclados:
                Teclado.Desconectar()
        if self.ModuloDeck:
            for deck in self.ListaDeck:
                deck.Desconectar()
        if self.ModuloMQTT:
            self.MQTT.Desconectar()
        # self.LimpiarDeck()
        # raise SystemExit
        os._exit(0)
