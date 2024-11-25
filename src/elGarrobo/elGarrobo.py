import os
import random
from pathlib import Path

from .acciones import CargarAcciones
from .accionesOOP import (
    accionActualizarPagina,
    accionAnteriorPagina,
    accionBase,
    accionEntrarFolder,
    accionRegresarFolder,
    accionSalir,
    accionSiquientePagina,
    cargarAcciones,
)
from .accionesOOP.heramientas.valoresAccion import valoresAcciones
from .dispositivos.mideck.mi_deck_extra import DefinirFuente, DefinirImagenes
from .dispositivos.mideck.mi_streamdeck import MiStreamDeck
from .dispositivos.migui.migui import miGui
from .dispositivos.mimqtt.mi_mqtt import MiMQTT
from .dispositivos.mipedal.mi_pedal import MiPedal
from .dispositivos.miteclado.mi_teclado_macro import MiTecladoMacro
from .miLibrerias import (
    ConfigurarLogging,
    ObtenerListaArhivos,
    ObtenerListaFolder,
    ObtenerValor,
    RelativoAbsoluto,
    SalvarArchivo,
    SalvarValor,
    UnirPath,
    leerData,
    obtenerArchivoPaquete,
)
from .modulos.mi_obs import MiOBS
from .modulos.mi_pulse import MiPulse

logger = ConfigurarLogging(__name__)


class color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class elGarrobo(object):
    """Clase base de Sistema de Macro ElGarrobo de ChepeCarlos."""

    def __init__(self) -> None:

        logger.info(f"Abri[config]")

        self.Data = obtenerArchivoPaquete("elGarrobo", "data/config.md")
        if self.Data is None:
            logger.error("No existe archivo Interno config.md")
            os._exit(0)

        self.DataUsuario = leerData("config")
        if self.DataUsuario is not None:
            logger.info("Cargando config usuario")
            if self.Data:
                self.Data |= self.DataUsuario
            else:
                self.Data = self.DataUsuario

        self.acciones = dict()

        self.IniciarModulo()

        if self.ModuloGui:
            self.miGui = miGui()
            self.miGui.ejecutaEvento = self.EjecutandoEvento
            self.miGui.salvarAcciones = self.salvarAcciones

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

            # TODO: recivir acciones desde Modulo de Pulse
            self.miGui.agregarAcciones(("salvar_pulse", "volumen", "mute"))
        if self.ModuloGui:
            self.miGui.iniciar()
            # TODO: cargar foldrer al inicio
            self.miGui.actualizarFolder(self.PathActual)

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
        self.ModuloGui = False

        if Modulos is not None:
            if "obs_notificacion" in Modulos:
                self.ModuloOBSNotificacion = Modulos["obs_notificacion"]

            if Modulos.get("monitor_esp", False):
                self.ModuloMonitorESP = leerData("modulos/monitor_esp/mqtt")

            self.ModuloOBS = Modulos.get("obs", False)
            self.ModuloDeck = Modulos.get("deck", False)
            self.ModuloTeclado = Modulos.get("teclado", False)
            self.ModuloPedal = Modulos.get("pedal", False)
            self.ModuloMQTT = Modulos.get("mqtt", False)
            self.ModuloMQTTEstado = Modulos.get("mqtt_estado", False)
            self.ModuloPulse = Modulos.get("pulse", False)
            self.ModuloAlias = Modulos.get("alias", False)
            self.ModuloGui = Modulos.get("gui", False)

    def IniciarAcciones(self):
        """
        Inicializa las acciones del Sistema en dict nombre de la accion y la funcion asociada
        """
        logger.info("ElGarrobo[Acciones] Cargando")

        accionSalir.funcionExterna = self.Salir
        accionEntrarFolder.funcionExterna = self.Entrar_Folder
        accionRegresarFolder.funcionExterna = self.Regresar_Folder

        ListaAcciones = CargarAcciones()
        listaClasesAcciones = cargarAcciones()

        # Acciones Macro
        ListaAcciones["macro"] = self.AccionesMacros
        ListaAcciones["presionar"] = self.AccionesPresionar  # TODO: ver lista que puede usar estado
        ListaAcciones["alias"] = self.AccionesAlias
        ListaAcciones["random"] = self.AccionRandom

        # Acciones Sistema
        ListaAcciones["reiniciar_data"] = self.Reiniciar

        # Acciones Deck
        if self.ModuloDeck:
            accionSiquientePagina.funcionExterna = self.Siquiente_Pagina
            accionAnteriorPagina.funcionExterna = self.Anterior_Pagina
            accionActualizarPagina.funcionExterna = self.Actualizar_Folder
            ListaAcciones["deck_brillo"] = self.DeckBrillo

        self.ListaAcciones = ListaAcciones
        self.listaClasesAcciones = listaClasesAcciones

        if self.ModuloGui:
            listaAccion = []
            for accion in self.ListaAcciones.keys():
                listaAccion.append(accion)
            for accion in self.listaClasesAcciones.keys():
                objetoAccion = self.listaClasesAcciones[accion]()
                nombreAccion = objetoAccion.nombre
                listaAccion.append(nombreAccion)
            self.miGui.listaAccionesOPP = self.listaClasesAcciones
            self.miGui.agregarAcciones(listaAccion)

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
                    # TODO: informar en archivo de configuración que están unidos
                    if self.ModuloGui:
                        nombre = "streamdeck"
                        archivo = "streamdeck.md"
                        input = "??"
                        pedal = {"nombre": nombre, "tipo": "steamdeck", "clase": "null", "input": input, "archivo": archivo}
                        self.miGui.agregarDispositivos(pedal)
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
                    if self.ModuloGui:
                        for teclado in self.Data["teclados"]:
                            nombre = teclado.get("nombre")
                            archivo = teclado.get("file")
                            input = teclado.get("input")
                            teclado = {"nombre": nombre, "tipo": "teclado", "clase": "null", "input": input, "archivo": archivo, "estado": True}
                            self.miGui.agregarDispositivos(teclado)
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
                    if self.ModuloGui:
                        for pedal in self.Data["pedal"]:
                            nombre = pedal.get("nombre")
                            archivo = pedal.get("file")
                            input = pedal.get("serial")
                            pedal = {"nombre": nombre, "tipo": "pedal", "clase": "null", "input": input, "archivo": archivo, "estado": True}
                            self.miGui.agregarDispositivos(pedal)
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
            if self.ModuloGui:
                self.miGui.actualizarFolder(self.PathActual)

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
        Carga recursivamente las configuración de los diferentes eventos por dispositivos.
        """
        ListaFolder = ObtenerListaFolder(Data["folder_path"])
        ListaArchivos = ObtenerListaArhivos(Data["folder_path"])

        if ListaArchivos is not None:
            for Archivo in ListaArchivos:
                tipoArchivo = Path(Archivo).suffix
                if tipoArchivo in [".md", ".json"]:
                    ArchivoSin = Path(Archivo).stem

                    encontrado = False
                    if self.ModuloTeclado:
                        encontrado = self.CargarArchivos("teclados", Data, ArchivoSin)
                    if self.ModuloDeck and not encontrado:
                        encontrado = encontrado or self.CargarArchivos("global", Data, ArchivoSin)
                        encontrado = encontrado or self.CargarArchivos("deck", Data, ArchivoSin)
                    if self.ModuloPedal and not encontrado:
                        encontrado = encontrado or self.CargarArchivos("pedal", Data, ArchivoSin)
                    if not encontrado:
                        logger.warning(f"No sabe importar {tipoArchivo} - {Archivo} - {Data['folder_path']}")

                elif tipoArchivo in [".gif", ".png", ".jpg", ".svg"]:  # no hacer nada con imágenes
                    pass
                elif tipoArchivo in [".wav", ".mp3"]:  # no hacen nada con audios
                    pass
                else:
                    logger.warning(f" No sabe importar {tipoArchivo} - {Archivo} - {Data['folder_path']}")

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

        DataDispositivo = self.Data.get(Dispositivo)

        for ArchivoDispositivo in DataDispositivo:
            fileDispositivo = ArchivoDispositivo.get("file")
            fileDispositivo = Path(fileDispositivo).stem
            if fileDispositivo == Archivo:
                Ruta = UnirPath(Data["folder_path"], fileDispositivo)
                Info = leerData(Ruta)

                Atributo = ArchivoDispositivo.get("nombre")
                if Info is not None:
                    Data[Atributo] = Info
                    return True
                else:
                    logger.warning(f"{color.RED}Error cargando: {Ruta}{color.END}")

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
            if self.ModuloGui:
                self.miGui.actualizarIconos = self.ActualizarDeck
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
            for infoPedales in self.Data.get("pedal"):
                pedalActual = MiPedal(infoPedales, self.Evento)
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

    def BuscarFolder(self, folder: str):
        ListaDispositivo = ["teclados", "global", "deck", "pedal"]
        Data = self.Keys
        folderes = folder.split("/")

        Mensaje = {"folder": folder}
        self.mensajeMonitorESP(Mensaje, "folder")

        if folderes:
            Data = self.BuscarDentroFolder(folderes, Data)
            if Data is not None:
                Encontrado = False
                for Dispositivo in ListaDispositivo:
                    Estado = self.CargarAcciones(Dispositivo, Data)
                    Encontrado = Estado or Encontrado

                if Encontrado:
                    if "streamdeck" in self.acciones:
                        self.desfaceDeck = 0
                return Encontrado

    def CargarAcciones(self, Dispositivo, Data):
        # TODO: quitar Data y self.Data
        Estado = False
        dispositivoActual = self.Data.get(Dispositivo)
        if dispositivoActual is not None:
            for dispositivo in dispositivoActual:
                nombreDispositivo = dispositivo.get("nombre")
                accionesDispositivo = Data.get(nombreDispositivo)
                if accionesDispositivo:
                    logger.info(f"Folder[Configurado] {nombreDispositivo}")
                    self.acciones[nombreDispositivo] = accionesDispositivo
                    if self.ModuloGui:
                        self.miGui.actualizarAcciones(nombreDispositivo, accionesDispositivo, self.PathActual)
                    Estado = True
        return Estado

    def BuscarDentroFolder(self, Folderes, Data):
        nombreFolder = Data.get("nombre")

        if nombreFolder is not None:
            if nombreFolder == Folderes[0]:
                Folderes.remove(nombreFolder)
                if Folderes:
                    dataFolder = Data.get("folder")
                    if dataFolder is not None:
                        for BuscarFolder in dataFolder:
                            Data = self.BuscarDentroFolder(Folderes, BuscarFolder)
                            if Data is not None:
                                return Data
                else:
                    return Data
        return None

    def Evento(self, Evento):
        NombreEvento = Evento.get("nombre")
        if NombreEvento in self.acciones:
            for accion in self.acciones[NombreEvento]:
                if "key" in accion:
                    if accion["key"] == Evento["key"]:
                        if Evento["estado"] == "presionado":
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
                estadoEvento = Evento.get("estado")
                if estadoEvento:
                    logger.info(f"Evento[No asignado] streamdeck[{key_desface}]")
                return
            else:
                pass
        else:
            pass

        estadoEvento = Evento.get("estado")
        if estadoEvento == "presionado":
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
                teclaAccion = accion.get("key")
                nombreAccion = accion.get("nombre")
                logger.info(f"AccionOOP[{comandoAccion}] - {nombreAccion}")

                Mensaje = {"accion": comandoAccion}
                if nombreAccion:
                    Mensaje["nombre"] = nombreAccion
                if teclaAccion:
                    Mensaje["key"] = teclaAccion

                self.mensajeMonitorESP(Mensaje, "accion")

                objetoAccion = self.listaClasesAcciones[comandoAccion]()
                objetoAccion.configurar(opcionesAccion)
                return objetoAccion.ejecutar()

        if "accion" in accion:
            comandoAccion = accion["accion"]
            if comandoAccion in self.ListaAcciones:
                opcionesAccion = dict()
                Nombre = None
                presionado = accion.get("__estado")
                nombreAccion = accion.get("nombre")
                teclaAccion = accion.get("key")

                if nombreAccion:
                    if isinstance(presionado, str):
                        logger.info(f"Accion[{comandoAccion}-{presionado}] - {Nombre}")
                    else:
                        logger.info(f"Accion[{comandoAccion}] - {Nombre}")
                else:
                    logger.info(f"Accion[{comandoAccion}]")

                if "opciones" in accion:
                    opcionesAccion = accion["opciones"]

                # TODO solo recibir opciones como lista o dicionario
                # if NombreAccion == "macro":
                #     print(type(opcionesAccion))
                if isinstance(opcionesAccion, dict):
                    opcionesAccion.update({"__estado": presionado})
                elif isinstance(opcionesAccion, list):
                    # TODO: agregar
                    for opciones in opcionesAccion:
                        opciones["__estado"] = presionado
                print()
                print("opciones:", opcionesAccion)

                # opcionesAccion.append({"__estado": presionado})

                Mensaje = {"accion": comandoAccion}
                if nombreAccion:
                    Mensaje["nombre"] = nombreAccion
                if teclaAccion:
                    Mensaje["key"] = teclaAccion

                self.mensajeMonitorESP(Mensaje, "accion")

                # try:
                return self.ListaAcciones[comandoAccion](opcionesAccion)
                # except Exception as Error:
                #     logger.info(f"Accion[Error] {Error}")
            else:
                logger.info(f"Accion[No Encontrada] {comandoAccion}")
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

    def Regresar_Folder(self, opciones: list):
        Direcion = self.PathActual.split("/")
        self.PathActual = "/".join(Direcion[:-1])
        if self.PathActual == "":
            self.PathActual = "defaul"
            return
        logger.info(f"Regresar[{self.PathActual}]")
        encontrado = self.BuscarFolder(self.PathActual)
        if encontrado:
            if self.ModuloDeck:
                self.LimpiarDeck()
                self.ActualizarDeck()
            if self.ModuloGui:
                self.miGui.actualizarFolder(self.PathActual)
        else:
            logger.warning(f"Regresar[En base]")

    def Entrar_Folder(self, opciones: list[valoresAcciones]):
        """
        Entra en folder
        """
        folder: str = self.obtenerValor(opciones, "folder")
        if folder is None:
            logger.warning(f"Folder[no encontrado]")
            return

        rutaActual = RelativoAbsoluto(folder, self.PathActual)
        if rutaActual == self.PathActual:
            logger.info(f"Folder[{rutaActual}] Actual")
            return
        copiaPath = self.PathActual
        self.PathActual = rutaActual
        encontrado = self.BuscarFolder(rutaActual)
        if encontrado:
            logger.info(f"Folder[{folder}]")
            if self.ModuloDeck:
                self.LimpiarDeck()
                self.ActualizarDeck()
            if self.ModuloGui:
                self.miGui.actualizarFolder(self.PathActual)

        else:
            logger.warning(f"Folder[{folder}] No encontró")
            self.PathActual = copiaPath

    def Actualizar_Folder(self, opciones: list[valoresAcciones]):
        self.ActualizarDeck()

    def Siquiente_Pagina(self, opciones: list[valoresAcciones]):
        self.MoverPagina("siquiente")

    def Anterior_Pagina(self, opciones: list[valoresAcciones]):
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
        # self.Data = obtenerArchivoPaquete("elGarrobo", "data/config.md")
        # if self.Data is None:
        #     logger.error("No existe archivo config.md")
        #     os._exit(0)

        folderAnterior = self.PathActual
        self.DataUsuario = leerData("config")
        if self.DataUsuario is not None:
            logger.info("Cargando config usuario")
            self.Data |= self.DataUsuario
        # TODO: Cargar modulos?
        self.acciones = dict()
        self.CargarData()
        self.PathActual = self.Data.get("folder_path")
        if self.ModuloGui:
            self.miGui.actualizarFolder(self.PathActual)
        self.BuscarFolder(self.PathActual)
        # TODO: no necesario reiniciar streamdeck
        self.Entrar_Folder([valoresAcciones("folder", folderAnterior)])
        self.PathActual = folderAnterior
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

    def Salir(self, opciones: list) -> None:
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

    def SolisitarNotifiacacion(self, texto, opciones: dict[valoresAcciones]):
        if self.ModuloOBSNotificacion:
            objetoAccion = self.listaClasesAcciones["notificacion"]()
            objetoAccion.configurar({"texto": texto})
            objetoAccion.ejecutar()

            if opciones is None:
                logger.error("error en configuracciones")
            else:
                opciones["mensaje"] = texto
                accionMQTT = self.listaClasesAcciones["mqtt"]()
                accionMQTT.configurar(opciones)
                accionMQTT.ejecutar()

    def salvarAcciones(self, acciones: list, dispositivo: list, folder: str):
        nombreDispositivo = dispositivo.get("nombre")
        ListaDispositivos = ["teclados", "global", "deck", "pedal"]
        for tipo in ListaDispositivos:
            dataDispositivos = self.Data.get(tipo)
            if dataDispositivos is None:
                continue
            for dataActual in dataDispositivos:
                if nombreDispositivo == dataActual.get("nombre"):
                    archivoDipositivos = f"{folder}/{dataActual.get('file')}"
                    accionesSalvar = list()
                    for accionesActual in acciones:
                        if isinstance(accionesActual, list):
                            print("falta para lista")
                        elif isinstance(accionesActual, dict):
                            accionNueva = dict()
                            for propiedad, valor in accionesActual.items():
                                if "__" in propiedad:
                                    continue
                                accionNueva[propiedad] = valor
                            accionesSalvar.append(accionNueva)
                    SalvarArchivo(archivoDipositivos, accionesSalvar)
                    self.ReiniciarData()
                    return

    def obtenerValor(self, listaValores: list[valoresAcciones], atributo: str):
        """Devuelve el valores configurado"""
        for valor in listaValores:
            if atributo == valor.atributo:
                return valor.valor

    def mensajeMonitorESP(self, mensaje: dict, tema: str):
        """Envia mensaje por mqtt de las acciones del ElGarrobo"""
        if self.ModuloMonitorESP:
            topicBase = self.ModuloMonitorESP.get("topic")
            if topicBase:
                opciones = {
                    "mensaje": mensaje,
                    "topic": f"{topicBase}/{tema}",
                }
                AccionMQTT = self.listaClasesAcciones["mqtt"]()
                AccionMQTT.configurar(opciones)
                AccionMQTT.ejecutar()
            else:
                logger.warning("Falta Topic en Modulo MonitorESP")
