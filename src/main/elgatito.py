import os
import random

from acciones import CargarAcciones
from dispositivos.mideck.mi_deck_extra import DefinirFuente, DefinirImagenes
from dispositivos.mideck.mi_streamdeck import MiStreamDeck
from dispositivos.mimqtt.mi_mqtt import MiMQTT
from dispositivos.miteclado.mi_teclado_macro import MiTecladoMacro
from extras.mi_obs import MiOBS
from extras.pulse import MiPulse
from MiLibrerias import (
    ConfigurarLogging,
    ObtenerArchivo,
    ObtenerListaArhivos,
    ObtenerListaFolder,
    ObtenerValor,
    RelativoAbsoluto,
    SalvarArchivo,
    SalvarValor,
    UnirPath,
)

logger = ConfigurarLogging(__name__)


class ElGatito(object):
    """Clase base de Sistema de Macro ElGatoALSW."""

    def __init__(self):

        logger.info(f"Configurando[config.json]")

        self.Data = ObtenerArchivo("config.json")
        if self.Data is None:
            logger.error("No existe archivo config.json")
            os._exit(0)

        self.acciones = dict()

        self.IniciarModulo()

        self.CargarData()

        self.IniciarAcciones()

        self.BuscarFolder(self.PathActual)

        if self.ModuloOBS:
            self.CargarOBS()

        if self.ModuloPulse:
            self.CargarPulse()

        if self.ModuloDeck:
            self.CargarStreamDeck()
            self.IniciarStreamDeck()

        if self.ModuloTeclado:
            self.CargarTeclados()

        if self.ModuloMQTT:
            self.IniciarMQTT()

        if self.ModuloPulse:
            self.ListaAcciones["salvar_pulse"]({})

    def IniciarModulo(self):
        """
        Carga los modulos activos.
        """
        logger.info(f"Configurando[Modulos]")
        Modulos = ObtenerArchivo("modulos/modulos.json")

        self.ModuloOBS = False
        self.ModuloOBSNotificacion = False
        self.ModuloDeck = False
        self.ModuloTeclado = False
        self.ModuloMQTT = False
        self.ModuloMQTTEstado = False
        self.ModuloPulse = False
        self.ModuloMonitorESP = False

        if Modulos is not None:
            if "obs" in Modulos:
                self.ModuloOBS = Modulos["obs"]

            if "obs_notificacion" in Modulos:
                self.ModuloOBSNotificacion = Modulos["obs_notificacion"]

            if "deck" in Modulos:
                self.ModuloDeck = Modulos["deck"]

            if "teclado" in Modulos:
                self.ModuloTeclado = Modulos["teclado"]

            if "mqtt" in Modulos:
                self.ModuloMQTT = Modulos["mqtt"]

            if "monitor_esp" in Modulos:
                if Modulos["monitor_esp"]:
                    self.ModuloMonitorESP = ObtenerArchivo("modulos/monidor_esp/mqtt.json")

            if "mqtt_estado" in Modulos:
                self.ModuloMQTTEstado = Modulos["mqtt_estado"]

            if "pulse" in Modulos:
                self.ModuloPulse = Modulos["pulse"]

    def IniciarAcciones(self):
        """
        Inicializa las acciones del Sistema en dict nombre de la accion y la funcion asociada
        """
        logger.info("ElGatoALSW[Acciones] Cargando")
        ListaAcciones = CargarAcciones()

        # Acciones Macro
        ListaAcciones["macro"] = self.AccionesMacros
        ListaAcciones["random"] = self.AccionRandom

        # Acciones Sistema
        ListaAcciones["salir"] = self.Salir
        ListaAcciones["reiniciar_data"] = self.Reiniciar
        ListaAcciones["entrar_folder"] = self.Entrar_Folder
        ListaAcciones["regresar_folder"] = self.Regresar_Folder

        # Acciones Deck
        if self.ModuloDeck:
            ListaAcciones["siquiente_pagina"] = self.Siquiente_Pagina
            ListaAcciones["anterior_pagina"] = self.Anterior_Pagina
            ListaAcciones["actualizar_pagina"] = self.Actualizar_Folder
            ListaAcciones["deck_brillo"] = self.DeckBrillo

        self.ListaAcciones = ListaAcciones

    def CargarData(self):
        """
        Cargando Data para Dispisitivo.
        """
        logger.info("Cargando[Eventos]")
        if self.ModuloDeck:
            self.BanderaActualizarDeck = False
            if "deck_file" in self.Data:
                DataDeck = ObtenerArchivo(self.Data["deck_file"])
                if DataDeck is not None:
                    self.Data["deck"] = DataDeck

        if self.ModuloTeclado:
            if "teclados_file" in self.Data:
                ArchivoTeclado = self.Data["teclados_file"]
                DataTeclado = ObtenerArchivo(ArchivoTeclado)
                if DataTeclado is not None:
                    self.Data["teclados"] = DataTeclado

        if "folder_path" in self.Data:
            self.PathActual = self.Data["folder_path"]
            self.Keys = {"nombre": self.Data["folder_path"], "folder_path": self.Data["folder_path"]}
            self.CargarFolder(self.Keys)

        if self.ModuloMQTT:
            if "mqtt_file" in self.Data:
                ArchivoMQTT = self.Data["mqtt_file"]
                DataMQTT = ObtenerArchivo(ArchivoMQTT)
                if DataMQTT is not None:
                    self.Data["mqtt"] = ObtenerArchivo(ArchivoMQTT)

    def CargarFolder(self, Data):
        """
        Carga recursivamente las configuracion de los diferentes eventos por dispositivos.
        """
        ListaFolder = ObtenerListaFolder(Data["folder_path"])
        ListaArchivos = ObtenerListaArhivos(Data["folder_path"])

        if ListaArchivos is not None:
            for Archivo in ListaArchivos:
                if self.ModuloTeclado:
                    self.CargarArchivos("teclados", Data, Archivo)
                if self.ModuloDeck:
                    self.CargarArchivos("global", Data, Archivo)
                    self.CargarArchivos("deck", Data, Archivo)

        if ListaFolder is not None:
            Data["folder"] = []
            for Folder in ListaFolder:
                pathActual = UnirPath(Data["folder_path"], Folder)
                data = {"nombre": Folder, "folder_path": pathActual}
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
                if ArchivoDispositivo["file"] == Archivo:
                    Ruta = UnirPath(Data["folder_path"], Archivo)
                    Info = ObtenerArchivo(Ruta)
                    Atributo = ArchivoDispositivo["nombre"]
                    if Info is not None:
                        Data[Atributo] = Info

    def CargarTeclados(self):
        """
        Confiurando Teclados Macros.
        """
        self.ListaTeclados = []
        if "teclados" in self.Data:
            logger.info("Teclados[Cargando]")
            for Teclado in self.Data["teclados"]:
                if "nombre" in Teclado and "input" in Teclado and "file" in Teclado:
                    TecladoActual = MiTecladoMacro(Teclado["nombre"], Teclado["input"], Teclado["file"], self.Evento)
                    TecladoActual.Conectar()
                    self.ListaTeclados.append(TecladoActual)

    def CargarStreamDeck(self):
        """Configurando streamdeck."""
        if "fuente" in self.Data:
            DefinirFuente(self.Data["fuente"])
            DefinirImagenes()
        if "deck" in self.Data:
            logger.info("StreamDeck[Cargando]")
            Cantidad_Base = 0
            self.ListaDeck = []
            for InfoDeck in self.Data["deck"]:
                DeckActual = MiStreamDeck(InfoDeck, self.Evento, Cantidad_Base)
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
            if "streamdeck" in self.acciones:
                Deck.CambiarFolder(self.PathActual)
                Deck.ActualizarIconos(self.acciones["streamdeck"], self.desfaceDeck, Unido=True)

            elif Deck.Nombre in self.acciones:
                Deck.CambiarFolder(self.PathActual)
                Deck.ActualizarIconos(self.acciones[Deck.Nombre], self.desfaceDeck)

    def ActualizarDeckIcono(self):

        # TODO: Problemar cuando funcion se llama muchas veces el gifs empieza a fallar
        if self.ListaDeck is not None:
            for Deck in self.ListaDeck:
                if "streamdeck" in self.acciones:
                    Deck.ActualizarIconos(self.acciones["streamdeck"], self.desfaceDeck, Unido=True)

                elif Deck.Nombre in self.acciones:
                    Deck.ActualizarIconos(self.acciones[Deck.Nombre], self.desfaceDeck)

    def LimpiarDeck(self):
        for Deck in self.ListaDeck:
            if "streamdeck" in self.acciones:
                Deck.Limpiar()
            elif Deck.Nombre in self.acciones:
                Deck.Limpiar()

    def BuscarFolder(self, Folder):
        ListaDispositivo = ["teclados", "global", "deck"]
        Data = self.Keys
        Folderes = Folder.split("/")

        FolderActual = Folderes[-1]
        if self.ModuloMonitorESP:
            if "topic" in self.ModuloMonitorESP:
                Mensaje = {"folder": FolderActual, "direccion": Folder}
                opciones = {"opciones": Mensaje, "topic": f"{self.ModuloMonitorESP['topic']}/folder"}
                self.ListaAcciones["mqtt"](opciones)

        if Folderes:
            Data = self.BuscarDentroFolder(Folderes, Data)
            if Data is not None:
                Encontrado = False
                for Dispositivo in ListaDispositivo:
                    Estado = self.CargarAcciones(Dispositivo, Data)
                    Encontrado = Estado or Encontrado
        if "streamdeck" in self.acciones:
            self.desfaceDeck = 0
            # TODO Error cuando no entra a streamdeck

    def CargarAcciones(self, Dispositivo, Data):
        # TODO: quitar Data y self.Data
        Estado = False
        if Dispositivo in self.Data:
            for dispositivo in self.Data[Dispositivo]:
                nombreDispositivo = dispositivo["nombre"]
                if nombreDispositivo in Data:
                    logger.info(f"Folder[Configurado] {nombreDispositivo}")
                    self.acciones[nombreDispositivo] = Data[nombreDispositivo]
                    Estado = True
        return Estado

    def BuscarDentroFolder(self, Folderes, Data):
        if "nombre" in Data:
            if Data["nombre"] == Folderes[0]:
                Folderes.remove(Data["nombre"])
                if Folderes:
                    if "folder" in Data:
                        for BuscarFolder in Data["folder"]:
                            Data = self.BuscarDentroFolder(Folderes, BuscarFolder)
                            if Data is not None:
                                return Data
                else:
                    return Data

    def Evento(self, Evento):
        NombreEvento = Evento["nombre"]
        if NombreEvento in self.acciones:
            for accion in self.acciones[NombreEvento]:
                if "key" in accion:
                    if accion["key"] == Evento["key"]:
                        if Evento["estado"]:
                            logger.info(f"Evento {NombreEvento}[{accion['key']}] {accion['nombre']}")
                        self.EjecutandoEvento(accion, Evento["estado"])
                        return

        if "deck" in Evento:
            if "streamdeck" in self.acciones:
                key_desface = Evento["key"] + Evento["base"] + self.desfaceDeck
                for accion in self.acciones["streamdeck"]:
                    if "key" in accion:
                        if accion["key"] == key_desface:
                            self.EjecutandoEvento(accion, Evento["estado"])
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
            if "accion" in evento:
                evento["precionado"] = estado
                # TODO: Ver como pasar estado entre macros
                self.BuscarAccion(evento)
            else:
                logger.info("Evento[no accion]")

    def BuscarAccion(self, accion):
        if "accion" in accion:
            NombreAccion = accion["accion"]
            if NombreAccion in self.ListaAcciones:
                opcionesAccion = {}
                Nombre = None

                if "nombre" in accion:
                    Nombre = accion["nombre"]
                    logger.info(f"Accion[{NombreAccion}] - {Nombre}")
                else:
                    logger.info(f"Accion[{NombreAccion}]")

                if "opciones" in accion:
                    opcionesAccion = accion["opciones"]

                # TODO: Mover a funcion aparte
                if self.ModuloMonitorESP:
                    if "topic" in self.ModuloMonitorESP:
                        Mensaje = {"accion": NombreAccion}
                        if "key" in accion:
                            Mensaje["key"] = accion["key"]
                        if Nombre is not None:
                            Mensaje["nombre"] = Nombre

                        opciones = {"opciones": Mensaje, "topic": f"{self.ModuloMonitorESP['topic']}/accion"}

                        self.ListaAcciones["mqtt"](opciones)

                # try:
                return self.ListaAcciones[NombreAccion](opcionesAccion)
                # except Exception as Error:
                #     logger.info(f"Accion[Error] {Error}")
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
        Cajon = {}
        for Numero, Comando in enumerate(ListaComando):

            logger.info(f"Macro[{Numero}]")

            if "macro_opciones" in Comando:
                macro_opciones = Comando["macro_opciones"]
                if "solisita" in macro_opciones:
                    atributo = macro_opciones["solisita"]
                    if atributo in Cajon:
                        if not "opciones" in Comando:
                            Comando["opciones"] = {}

                        atributoRecibir = atributo
                        if "solisita_cambiar" in macro_opciones:
                            atributoRecibir = macro_opciones["solisita_cambiar"]

                        opciones = Comando["opciones"]
                        opciones[atributoRecibir] = Cajon[atributo]
                        logger.info(f"Cargar_cajon[{atributoRecibir}] {opciones}")

            respuesta = self.BuscarAccion(Comando)

            if "macro_opciones" in Comando:
                macro_opciones = Comando["macro_opciones"]
                if "respuesta" in macro_opciones:
                    atributo = macro_opciones["respuesta"]
                    Cajon[atributo] = respuesta
                    logger.info(f"Salvar_Cajon[{atributo}] {respuesta}")

        # TODO: Hacer Macros en diferentes Hilos

    def AccionRandom(self, opciones):
        """
        Ejecuta una accion al azar de una lista de acciones
        """
        logger.info("Lanzando Datos")
        Selecion = random.choice(opciones)
        return self.BuscarAccion(Selecion)

    def Reiniciar(self, opciones):
        """
        Reinicia la data del programa.
        """
        logger.info("Reiniciar data ElGatoALSW")
        self.ReiniciarData()

    def Regresar_Folder(self, opciones):
        Direcion = self.PathActual.split("/")
        self.PathActual = "/".join(Direcion[:-1])
        if self.PathActual == "":
            self.PathActual = "defaul"
            return
        logger.info(f"Regresar[{self.PathActual}]")
        self.BuscarFolder(self.PathActual)
        if self.ModuloDeck:
            self.LimpiarDeck()
            self.ActualizarDeck()

    def Entrar_Folder(self, opciones):
        """
        Entra en folder

        folder -> str
            folder a entrar
        """
        if "folder" in opciones:
            Folder = opciones["folder"]
        else:
            logger.warning(f"Folder[no encontrado]")
            return
        logger.info(f"Folder[{Folder}]")
        self.PathActual = RelativoAbsoluto(Folder, self.PathActual)
        self.BuscarFolder(self.PathActual)
        if self.ModuloDeck:
            self.LimpiarDeck()
            self.ActualizarDeck()

    def Actualizar_Folder(self, opciones):
        self.ActualizarDeck()

    def Siquiente_Pagina(self, opciones):
        self.MoverPagina("siquiente")

    def Anterior_Pagina(self, opciones):
        self.MoverPagina("anterior")

    def DeckBrillo(self, opciones):
        Brillo = ObtenerValor("data/streamdeck.json", "brillo")

        def constrain(n, minn, maxn):
            return max(min(maxn, n), minn)

        if "cantidad" in opciones:
            cantidad = opciones["cantidad"]
        else:
            return
        Brillo += cantidad
        Brillo = constrain(Brillo, 0, 100)
        logger.info(f"Deck[Brillo]: {Brillo}")
        SalvarValor("data/streamdeck.json", "brillo", Brillo)
        for deck in self.ListaDeck:
            deck.Brillo(Brillo)

    def MoverPagina(self, Direcion):
        if "streamdeck" in self.acciones:
            UltimoDeck = self.ListaDeck[-1]
            Cantidad = UltimoDeck.Base + UltimoDeck.Cantidad
            UltimaAccion = max(self.acciones["streamdeck"], key=lambda x: int(x["key"]))
            # TODO Limpiar codigo sucio
            if Direcion == "siquiente":
                self.desfaceDeck += Cantidad
                if self.desfaceDeck - 1 >= UltimaAccion["key"]:
                    self.desfaceDeck -= Cantidad
                    return
                logger.info("Deck[Siquiente Pagina]")
            elif Direcion == "anterior":
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
        if self.ModuloDeck:
            self.LimpiarDeck()
            self.ActualizarDeck()

    def IniciarMQTT(self):
        """Iniciar coneccion con Broker MQTT."""
        self.ListaMQTT = []
        self.Data["mqtt"] = ObtenerArchivo("mqtt.json")
        if "mqtt" in self.Data:
            for DataMQTT in self.Data["mqtt"]:
                ServidorMQTT = MiMQTT(DataMQTT, self.BuscarAccion)
                self.ListaMQTT.append(ServidorMQTT)
            for ServidorMQTT in self.ListaMQTT:
                ServidorMQTT.Conectar()

    def ReiniciarData(self):
        """
        Reinicia data de los Botones Actuales.
        """
        self.Data = ObtenerArchivo("config.json")
        # TODO: Cargar modulos?
        self.acciones = dict()
        self.CargarData()
        # TODO: Quitar Hard codign de defaul
        self.PathActual = "defaul"
        self.BuscarFolder(self.PathActual)
        self.IniciarStreamDeck()

    def CargarOBS(self):
        """
        Inicialioza el Objeto de OBS
        """
        self.OBS = MiOBS()
        self.OBS.DibujarDeck(self.SolisitarDibujar)
        self.OBS.AgregarNotificacion(self.SolisitarNotifiacacion)

        # Acciones OBS
        self.OBS.IniciarAcciones(self.ListaAcciones)

    def CargarPulse(self):
        """
        Inicialioza el Objeto de Pulse
        """
        self.Pulse = MiPulse()
        self.Pulse.DibujarDeck(self.SolisitarDibujar)
        self.Pulse.IniciarAcciones(self.ListaAcciones)

    def __exit__(self, exc_type, exc_value, traceback):
        print("Hora de matar todo XD")
        # for file in self.files:
        #     os.unlink(file)

    def __del__(self):
        print("I'm being automatically destroyed. Goodbye!")

    def Salir(self, opciones):
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
            for Servidor in self.ListaMQTT:
                Servidor.Desconectar()
        # self.LimpiarDeck()
        # raise SystemExit
        os._exit(0)

    def SolisitarDibujar(self):

        if self.ModuloDeck:
            self.BanderaActualizarDeck = True

            if self.BanderaActualizarDeck:
                self.ActualizarDeckIcono()
                self.BanderaActualizarDeck = False

    def SolisitarNotifiacacion(self, Texto):
        if self.ModuloOBSNotificacion:
            opciones = {"texto": Texto}
            self.ListaAcciones["notificacion"](opciones)
            # Temporal data a test.mosquitto.org
            opciones = {
                "servidor": "test.mosquitto.org",
                "puerto": 1883,
                "topic": "alsw/monitor_esp/obs",
                "mensaje": Texto,
            }
            self.ListaAcciones["mqtt"](opciones)
