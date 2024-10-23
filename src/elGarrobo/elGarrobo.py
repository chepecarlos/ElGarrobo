import os
import random

from .acciones import CargarAcciones
from .accionesOOP import cargarAcciones
from .dispositivos.mideck.mi_deck_extra import DefinirFuente, DefinirImagenes
from .dispositivos.mideck.mi_streamdeck import MiStreamDeck
from .dispositivos.mimqtt.mi_mqtt import MiMQTT
from .dispositivos.mipedal.mi_pedal import MiPedal
from .dispositivos.miteclado.mi_teclado_macro import MiTecladoMacro
from .miLibrerias import (
    ConfigurarLogging,
    ObtenerListaArhivos,
    ObtenerListaFolder,
    ObtenerValor,
    RelativoAbsoluto,
    SalvarValor,
    UnirPath,
    leerData,
    obtenerArchivoPaquete,
)
from .modulos.mi_obs import MiOBS
from .modulos.pulse import MiPulse

logger = ConfigurarLogging(__name__)


class elGarrobo(object):
    """Clase base de Sistema de Macro ElGarrobo de ChepeCarlos."""

    def __init__(self) -> None:

        logger.info(f"Abri[config]")

        self.Data = obtenerArchivoPaquete("elGarrobo", "elGarrobo/data/config.md")
        if self.Data is None:
            logger.error("No existe archivo Interno config.md")
            os._exit(0)

        self.DataUsuario = leerData("config")
        if self.DataUsuario is not None:
            logger.info("Cargando config usuario")
            self.Data |= self.DataUsuario

        self.acciones = dict()

        self.IniciarModulo()

        self.CargarData()

        self.IniciarAcciones()

        self.BuscarFolder(self.PathActual)

        if self.ModuloPedal or self.ModuloDeck:
            self.listaIndex = []

        if self.ModuloOBS:
            self.CargarOBS()

        if self.ModuloPulse:
            self.CargarPulse()

        if self.ModuloDeck:
            self.CargarStreamDeck()
            self.IniciarStreamDeck()

        if self.ModuloPedal:
            self.cargarPedal()

        if self.ModuloTeclado:
            self.cargarTeclados()

        if self.ModuloMQTT:
            self.IniciarMQTT()

        if self.ModuloPulse:
            self.ListaAcciones["salvar_pulse"]({})

    def IniciarModulo(self) -> None:
        """
        Carga los modulos activos.
        """
        logger.info(f"Configurando[Modulos]")
        Modulos = leerData("modulos/modulos")

        if Modulos is None:
            logger.error("No existe archivo modulos.md")
            os._exit(0)

        # TODO: Modulos en un dict

        self.ModuloOBS = False
        self.ModuloOBSNotificacion = False
        self.ModuloDeck = False
        self.ModuloTeclado = False
        self.ModuloMQTT = False
        self.ModuloMQTTEstado = False
        self.ModuloPulse = False
        self.ModuloMonitorESP = False
        self.ModuloAlias = False
        self.ModuloPedal = False

        if Modulos is not None:
            if "obs_notificacion" in Modulos:
                self.ModuloOBSNotificacion = Modulos["obs_notificacion"]

            if Modulos.get("monitor_esp", False):
                self.ModuloMonitorESP = leerData("modulos/monidor_esp/mqtt")

            self.ModuloOBS = Modulos.get("obs", False)
            self.ModuloDeck = Modulos.get("deck", False)
            self.ModuloTeclado = Modulos.get("teclado", False)
            self.ModuloPedal = Modulos.get("pedal", False)
            self.ModuloMQTT = Modulos.get("mqtt", False)
            self.ModuloMQTTEstado = Modulos.get("mqtt_estado", False)
            self.ModuloPulse = Modulos.get("pulse", False)
            self.ModuloAlias = Modulos.get("alias", False)

    def IniciarAcciones(self):
        """
        Inicializa las acciones del Sistema en dict nombre de la accion y la funcion asociada
        """
        logger.info("ElGarrobo[Acciones] Cargando")
        ListaAcciones = CargarAcciones()
        listaClasesAcciones = cargarAcciones()

        # Acciones Macro
        ListaAcciones["macro"] = self.AccionesMacros
        ListaAcciones["presionar"] = self.AccionesPresionar  # TODO: ver lista que puede usar estado
        ListaAcciones["alias"] = self.AccionesAlias
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
        self.listaClasesAcciones = listaClasesAcciones

    def CargarData(self):
        """
        Cargando Data para Dispisitivo.
        """
        logger.info("Cargando[Eventos]")
        if self.ModuloDeck:
            self.BanderaActualizarDeck = False
            deck_file = self.Data.get("deck_file")
            if deck_file is not None:
                DataDeck = leerData(deck_file)
                if DataDeck is not None:
                    self.Data["deck"] = DataDeck
                else:
                    logger.error(f"Falta {deck_file}")
            else:
                logger.error("Falta atribulo deck_file en config")

        if self.ModuloTeclado:
            teclados_file = self.Data.get("teclados_file")
            if teclados_file is not None:
                DataTeclado = leerData(teclados_file)
                if DataTeclado is not None:
                    self.Data["teclados"] = DataTeclado
                else:
                    logger.error(f"Falta {deck_file}")
            else:
                logger.error("Falta atribulo teclados_file en config")

        if self.ModuloPedal:
            pedal_file = self.Data.get("pedal_file")
            if pedal_file is not None:
                DataPedal = leerData(pedal_file)
                if DataPedal is not None:
                    self.Data["pedal"] = DataPedal
                else:
                    logger.error(f"Falta {pedal_file}")

        pathActual = self.Data.get("folder_path")
        if pathActual is not None:
            self.PathActual = pathActual
            self.Keys = {
                "nombre": self.Data["folder_path"],
                "folder_path": self.Data["folder_path"],
            }
            self.CargarFolder(self.Keys)

        ## TODO: por que no inicia la data de mqtt
        if self.ModuloMQTT:
            archivoMQTT = self.Data.get("mqtt_file")
            if archivoMQTT is not None:
                dataMQTT = leerData(archivoMQTT)
                if dataMQTT is not None:
                    self.Data["mqtt"] = dataMQTT

        if self.ModuloAlias:
            archivoAlias = self.Data.get("alias_file")
            if archivoAlias:
                dataAlias = leerData(archivoAlias)
                if dataAlias is not None:
                    self.Data["alias"] = dataAlias

    def CargarFolder(self, Data):
        """
        Carga recursivamente las configuracion de los diferentes eventos por dispositivos.
        """
        ListaFolder = ObtenerListaFolder(Data["folder_path"])
        ListaArchivos = ObtenerListaArhivos(Data["folder_path"])

        if ListaArchivos is not None:
            for Archivo in ListaArchivos:
                if ".md" in Archivo or ".json" in Archivo:
                    Archivo = Archivo.replace(".json", "")
                    Archivo = Archivo.replace(".md", "")
                    encontrado = False
                    if self.ModuloTeclado:
                        encontrado = self.CargarArchivos("teclados", Data, Archivo)
                    if self.ModuloDeck and not encontrado:
                        encontrado = encontrado or self.CargarArchivos("global", Data, Archivo)
                        encontrado = encontrado or self.CargarArchivos("deck", Data, Archivo)
                    if self.ModuloPulse and not encontrado:
                        self.CargarArchivos("pedal", Data, Archivo)

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
                fileDispositivo = ArchivoDispositivo.get("file")
                fileDispositivo = fileDispositivo.replace(".json", "")
                fileDispositivo = fileDispositivo.replace(".md", "")
                if fileDispositivo == Archivo:
                    Ruta = UnirPath(Data["folder_path"], fileDispositivo)
                    Info = leerData(Ruta)
                    Atributo = ArchivoDispositivo.get("nombre")
                    if Info is not None:
                        Data[Atributo] = Info
                        return True
        return False

    def cargarTeclados(self):
        """
        Configurando Teclados Macros.
        """
        self.ListaTeclados = []
        if "teclados" in self.Data:
            logger.info("Teclados[Cargando]")
            for teclado in self.Data["teclados"]:
                nombre = teclado.get("nombre")
                archivo = teclado.get("file")
                input = teclado.get("input")
                estado = teclado.get("enable", True)
                if estado:
                    if nombre is not None and archivo is not None and input is not None:
                        tecladoActual = MiTecladoMacro(nombre, input, archivo, self.Evento)
                        tecladoActual.Conectar()
                        self.ListaTeclados.append(tecladoActual)

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
                indexActual = DeckActual.Conectar(self.listaIndex)
                self.listaIndex.append(indexActual)
                Cantidad_Base += DeckActual.Cantidad
                self.ListaDeck.append(DeckActual)
            self.ListaDeck.sort(key=lambda x: x.id, reverse=False)
            #     self.ListaDeck.append(DeckActual)
            # CargarDeck = IniciarStreamDeck(self.Data['deck'], self.Evento)
            # for Deck in CargarDeck:
            #     DeckActual = MiStreamDeck(Deck)
        else:
            self.ListaDeck = None

    def cargarPedal(self):
        """Configura los Pedales de StreamDeck"""
        if "pedal" in self.Data:
            logger.info("Pedal[Cargando]")
            self.listaPedales = []
            for indoPedales in self.Data.get("pedal"):
                pedalActual = MiPedal(indoPedales, self.Evento)
                indexActual = pedalActual.conectar(self.listaIndex)
                self.listaIndex.append(indexActual)
                self.listaPedales.append(pedalActual)
            self.ListaDeck.sort(key=lambda x: x.id, reverse=False)
        else:
            self.listaPedales = None

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
        ListaDispositivo = ["teclados", "global", "deck", "pedal"]
        Data = self.Keys
        Folderes = Folder.split("/")

        FolderActual = Folderes[-1]
        if self.ModuloMonitorESP:
            if "topic" in self.ModuloMonitorESP:
                Mensaje = {"folder": FolderActual, "direccion": Folder}
                opciones = {
                    "opciones": Mensaje,
                    "topic": f"{self.ModuloMonitorESP['topic']}/folder",
                }
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
        dispositivoActual = self.Data.get(Dispositivo)
        if dispositivoActual is not None:
            for dispositivo in dispositivoActual:
                nombreDispositivo = dispositivo.get("nombre")
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
        NombreEvento = Evento.get("nombre")
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
                key_desface = Evento.get("key") + Evento.get("base", 0) + self.desfaceDeck
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

        if isinstance(estado, bool):
            if estado:
                if "accion" in evento:
                    evento["__estado"] = estado
                    # TODO: Ver como pasar estado entre macros
                    self.BuscarAccion(evento)
                else:
                    logger.info("Evento[no accion]")
        elif isinstance(estado, str):
            evento["__estado"] = estado
            accion = evento.get("accion")
            if accion == "presionar" or estado == "presionado":
                self.BuscarAccion(evento)

    def BuscarAccion(self, accion):
        comandoAccion = accion.get("accion")
        if comandoAccion is not None:
            if comandoAccion in self.listaClasesAcciones:
                print(f"intentando ejecutar OOP-{comandoAccion}")
                opcionesAccion = accion.get("opciones", {})
                nombreAccion = accion.get("nombre")
                logger.info(f"AccionOOP[{comandoAccion}] - {nombreAccion}")

                if self.ModuloMonitorESP:
                    if "topic" in self.ModuloMonitorESP:
                        Mensaje = {"accion": nombreAccion}
                        if "key" in accion:
                            Mensaje["key"] = accion["key"]
                        if nombreAccion is not None:
                            Mensaje["nombre"] = nombreAccion

                        opciones = {
                            "opciones": Mensaje,
                            "topic": f"{self.ModuloMonitorESP['topic']}/accion",
                        }

                        self.ListaAcciones["mqtt"](opciones)

                objetoAccion = self.listaClasesAcciones[comandoAccion]()
                objetoAccion.configurar(opcionesAccion)
                return objetoAccion.ejecutar()

        if "accion" in accion:
            NombreAccion = accion["accion"]
            if NombreAccion in self.ListaAcciones:
                opcionesAccion = dict()
                Nombre = None
                presionado = accion.get("__estado")

                if "nombre" in accion:
                    Nombre = accion["nombre"]
                    if isinstance(presionado, str):
                        logger.info(f"Accion[{NombreAccion}-{presionado}] - {Nombre}")
                    else:
                        logger.info(f"Accion[{NombreAccion}] - {Nombre}")
                else:
                    logger.info(f"Accion[{NombreAccion}]")

                if "opciones" in accion:
                    opcionesAccion = accion["opciones"]

                # TODO solo recibir opciones como lista o dicionario
                if isinstance(opcionesAccion, dict):
                    opcionesAccion.update({"__estado": presionado})
                elif isinstance(opcionesAccion, list):
                    opcionesAccion.append({"__estado": presionado})

                # TODO: Mover a funcion aparte
                if self.ModuloMonitorESP:
                    if "topic" in self.ModuloMonitorESP:
                        Mensaje = {"accion": NombreAccion}
                        if "key" in accion:
                            Mensaje["key"] = accion["key"]
                        if Nombre is not None:
                            Mensaje["nombre"] = Nombre

                        opciones = {
                            "opciones": Mensaje,
                            "topic": f"{self.ModuloMonitorESP['topic']}/accion",
                        }

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
        cajon = {}
        for numero, comando in enumerate(ListaComando):

            logger.info(f"Macro[{numero}]")

            self.solisitaMacro(comando, cajon)

            respuesta = self.BuscarAccion(comando)

            self.respuestaMacro(comando, respuesta, cajon)

        # TODO: Hacer Macros en diferentes Hilos

    def AccionesPresionar(self, opciones):

        estado = opciones.get("__estado")
        if estado is None:
            logger.info("Falta Estado en Accion Presionar")
            return

        accion = opciones.get(estado)

        if accion is None:
            return

        return self.BuscarAccion(accion)

    def AccionesAlias(self, opciones):
        """
        Ejecuta una accion con un sobre nombre
        """
        if not self.ModuloAlias:
            return

        nombre = opciones.get("nombre")
        if nombre is not None:
            for accion in self.Data["alias"]:
                if nombre == accion.get("nombre"):
                    self.BuscarAccion(accion)

    def solisitaMacro(self, comando, cajon):
        if "macro_opciones" in comando:
            macroOpciones = comando["macro_opciones"]
            if "solisita" in macroOpciones:
                atributo = macroOpciones["solisita"]
                Tipo = type(atributo)
                if Tipo is list:
                    recibir = atributo
                    if "solisita_cambiar" in macroOpciones:
                        recibir = macroOpciones["solisita_cambiar"]
                    for atributoTMP, recibirTMP in zip(atributo, recibir):
                        self.solisitudSimpleMacro(comando, atributoTMP, recibirTMP, cajon)
                else:
                    recibir = None
                    if "solisita_cambiar" in macroOpciones:
                        recibir = macroOpciones["solisita_cambiar"]
                    self.solisitudSimpleMacro(comando, atributo, recibir, cajon)

    def solisitudSimpleMacro(self, comando, atributo, recibir, cajon):
        if atributo in cajon:
            if not "opciones" in comando:
                comando["opciones"] = {}

            if recibir is None:
                recibir = atributo

            opciones = comando["opciones"]
            opciones[recibir] = cajon[atributo]
            logger.info(f"Cargar_cajon[{recibir}] {opciones}")

    def respuestaMacro(self, comando, respuesta, cajon):
        if "macro_opciones" in comando:
            macro_opciones = comando["macro_opciones"]
            if "respuesta" in macro_opciones:
                atributo = macro_opciones["respuesta"]
                cajon[atributo] = respuesta
                logger.info(f"Salvar_Cajon[{atributo}] {respuesta}")

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
        # TODO: no entrar a folder si no existe
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
        self.Data["mqtt"] = leerData("mqtt")
        # todo: no existe mqtt.json
        if "mqtt" in self.Data and self.Data["mqtt"] is not None:
            for DataMQTT in self.Data["mqtt"]:
                ServidorMQTT = MiMQTT(DataMQTT, self.BuscarAccion)
                self.ListaMQTT.append(ServidorMQTT)
            for ServidorMQTT in self.ListaMQTT:
                ServidorMQTT.Conectar()

    def ReiniciarData(self):
        """
        Reinicia data de los Botones Actuales.
        """
        self.Data = obtenerArchivoPaquete("elGarrobo", "elGarrobo/data/config.md")
        if self.Data is None:
            logger.error("No existe archivo config.md")
            os._exit(0)

        self.DataUsuario = leerData("config")
        if self.DataUsuario is not None:
            logger.info("Cargando config usuario")
            self.Data |= self.DataUsuario
        # TODO: Cargar modulos?
        self.acciones = dict()
        self.CargarData()
        self.PathActual = self.Data.get("folder_path")
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

    def SolisitarNotifiacacion(self, texto, opciones):
        if self.ModuloOBSNotificacion:
            objetoAccion = self.listaClasesAcciones["notificacion"]()
            objetoAccion.configurar({"texto": texto})
            objetoAccion.ejecutar()

            if opciones is None:
                logger.error("error en configuracciones")
            else:
                opciones["mensaje"] = texto
                self.ListaAcciones["mqtt"](opciones)
