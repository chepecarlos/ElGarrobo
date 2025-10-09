import os
import random
from pathlib import Path

from .acciones import CargarAcciones
from .accionesOOP import (
    accion,
    accionActualizarPagina,
    accionAnteriorPagina,
    accionEntrarFolder,
    accionPresionar,
    accionRecargarFolder,
    accionRegresarFolder,
    accionSalir,
    accionSiquientePagina,
    cargarClasesAcciones,
)
from .accionesOOP.heramientas.valoresAccion import valoresAcciones
from .dispositivos import MiMQTT, cargarDispositivos, dispositivo, miGui
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

    folderPerfil: str = "default"
    "Folder donde se buscan las acciones"

    listaDispositivos: list[dispositivo] = list()
    "Lista de dispositivos disponibles"
    listaClasesAcciones: dict[str,] = dict()
    ListaAcciones = None

    PathActual = None

    def __init__(self) -> None:

        logger.info(f"Abrí[config]")

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

        self.IniciarAcciones()
        self.iniciarDispositivos()

        if self.ModuloDeck:
            self.listaIndex = []

        if self.ModuloOBS:
            self.CargarOBS()

        if self.ModuloPulse:
            self.CargarPulse()

        if self.ModuloMQTT:
            self.IniciarMQTT()

        if self.ModuloPulse:
            self.ListaAcciones["salvar_pulse"]({})

            # TODO: recivir acciones desde Modulo de Pulse
            if self.ModuloGui:
                for dispositivo in self.listaDispositivos:
                    if dispositivo.nombre == "gui":
                        dispositivo.agregarAcciones(("salvar_pulse", "volumen", "mute"))

        if self.ModuloGui:
            for dispositivo in self.listaDispositivos:
                if dispositivo.tipo == "gui":
                    dispositivo.listaDispositivos = self.listaDispositivos
                    dispositivo.listaClasesAcciones = self.listaClasesAcciones
                    dispositivo.actualizar()

    def iniciarDispositivos(self):
        """Crea y inicializa los dispositivos que enviar las acciones"""
        self.dispositivosDisponibles: list[dispositivo] = cargarDispositivos()

        for claseDispositivo in self.dispositivosDisponibles:
            self.listaDispositivos.extend(claseDispositivo.cargarDispositivos(self.modulos, claseDispositivo))

        for dispositivo in self.listaDispositivos:
            dispositivo.configurarFuncionAccion(self.ejecutarAcción)
            dispositivo.asignarPerfil(self.folderPerfil)
            if dispositivo.activado and not dispositivo.conectado:
                dispositivo.cargarAccionesFolder("/")
                dispositivo.conectar()
                dispositivo.actualizar()

    def IniciarModulo(self) -> None:
        """
        Carga los modulos activos.
        """
        logger.info(f"Configurando[Modulos]")
        Modulos = leerData("modulos")
        self.modulos = Modulos

        if Modulos is None:
            logger.error("No existe archivo modulos.md")
            os._exit(0)

        # TODO: Modulos en un dict

        self.ModuloOBS = False
        self.ModuloOBSNotificacion = False
        self.ModuloDeck = False
        self.ModuloCombinado = False
        self.ModuloMQTT = False
        self.ModuloMQTTEstado = False
        self.ModuloPulse = False
        self.ModuloMonitorESP = False
        self.ModuloAlias = False
        self.ModuloGui = False

        if Modulos is not None:
            if "obs_notificacion" in Modulos:
                self.ModuloOBSNotificacion = Modulos["obs_notificacion"]

            if Modulos.get("monitor_esp", False):
                self.ModuloMonitorESP = leerData("modulos/monitor_esp/mqtt")

            self.ModuloOBS = Modulos.get("obs", False)
            self.ModuloCombinado = Modulos.get("deck_combinado", False)
            self.ModuloDeck = Modulos.get("deck", False)
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
        accionEntrarFolder.funcionExterna = self.entrar_Folder
        accionRegresarFolder.funcionExterna = self.regresar_Folder
        accionRecargarFolder.funcionExterna = self.Reiniciar
        accionPresionar.funcionExterna = self.accionesPresionar

        ListaAcciones = CargarAcciones()
        listaClasesAcciones = cargarClasesAcciones()

        # Acciones Macro
        ListaAcciones["macro"] = self.AccionesMacros
        ListaAcciones["alias"] = self.AccionesAlias
        ListaAcciones["random"] = self.AccionRandom

        # Acciones Deck
        if self.ModuloDeck or self.ModuloCombinado:
            accionSiquientePagina.funcionExterna = self.siquiente_Pagina
            accionAnteriorPagina.funcionExterna = self.anterior_Pagina
            accionActualizarPagina.funcionExterna = self.Actualizar_Folder
            ListaAcciones["deck_brillo"] = self.DeckBrillo

        self.ListaAcciones = ListaAcciones
        self.listaClasesAcciones = listaClasesAcciones

        # if self.ModuloGui:
        #     listaAccion = []
        #     for accion in self.ListaAcciones.keys():
        #         listaAccion.append(accion)
        #     for accion in self.listaClasesAcciones.keys():
        #         objetoAccion = self.listaClasesAcciones[accion]()
        #         nombreAccion = objetoAccion.nombre
        #         listaAccion.append(nombreAccion)

        #     for dispositivo in self.listaDispositivos:
        #         if dispositivo.tipo == "gui":
        #             dispositivo.listaClasesAccionesOPP = self.listaClasesAcciones
        #             dispositivo.agregarAcciones(listaAccion)
        # self.miGui.listaClasesAccionesOPP = self.listaClasesAcciones
        # self.miGui.agregarAcciones(listaAccion)

    # def cargarFolder(self):

    #     logger.info("Cargando acciones desde inicio")
    #     self.entrar_Folder({valoresAcciones("folder", "/")})

    def CargarData(self):
        """
        Cargando Data para Dispisitivo.
        """

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

    def ActualizarDeck(self):

        for dispositivo in self.listaDispositivos:
            if hasattr(dispositivo, "actualizarIconos"):
                logger.info(f"Se puede limpiar los iconos {dispositivo.nombre}")
                dispositivo.actualizarIconos()

    def LimpiarDeck(self):

        for dispositivo in self.listaDispositivos:
            if hasattr(dispositivo, "limpiarIconos"):
                logger.info(f"Se puede limpiar los iconos {dispositivo.nombre}")
                dispositivo.limpiarIconos()

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

    def Evento(self, Evento: dict):
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

        self.ejecutarAcción(evento, estado)
        # if isinstance(estado, bool):
        #     if estado:
        #         if "accion" in evento:
        #             evento["__estado"] = estado
        #             # TODO: Ver como pasar estado entre macros
        #         else:
        #             logger.info("Evento[no accion]")
        # elif isinstance(estado, str):
        #     evento["__estado"] = estado
        #     accion = evento.get("accion")
        #     if accion == "presionar" or estado == "presionado":
        #         self.ejecutarAcción(evento)

    def ejecutarAcción(self, accion: dict, estado: bool = True):
        """Ejecuta una acción según el comando y las opciones proporcionadas.

        Args:
            accion (dick):
            estado (bool, opcional):
        """
        comandoAccion: str = accion.get("accion")

        if comandoAccion is None:
            logger.info(f"Accion[No Atributo] - {accion}")
            return

        if comandoAccion in self.listaClasesAcciones:
            opcionesAccion: dict = accion.get("opciones", {})
            teclaAccion: str = accion.get("key")
            nombreAccion: str = accion.get("nombre")

            if comandoAccion == accionPresionar.comando:
                opcionesAccion["estado"] = estado
                estado = True

            if estado:
                logger.info(f"AccionOOP[{comandoAccion}] - {nombreAccion}")

                if self.ModuloMonitorESP:
                    Mensaje = {"accion": comandoAccion}
                    if nombreAccion:
                        Mensaje["nombre"] = nombreAccion
                    if teclaAccion:
                        Mensaje["key"] = teclaAccion

                    self.mensajeMonitorESP(Mensaje, "accion")

                objetoAccion: accion = self.listaClasesAcciones[comandoAccion]()
                objetoAccion.configurar(opcionesAccion)
                try:
                    return objetoAccion.ejecutar()
                except Exception as Error:
                    logger.exception(f"Accion[Error-{comandoAccion}] {Error}")
            return

        if self.ListaAcciones is None:
            return

        elif comandoAccion in self.ListaAcciones:

            if not estado:
                return

            opcionesAccion = dict()
            Nombre = None
            presionado = accion.get("__estado")
            nombreAccion = accion.get("nombre")
            teclaAccion = accion.get("key")

            if nombreAccion:
                if isinstance(presionado, str):
                    logger.info(f"Accion[{comandoAccion}-{presionado}] - {Nombre}")
                else:
                    if Nombre == None:
                        logger.info(f"Accion[{comandoAccion}]")
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

            if self.ModuloMonitorESP:
                Mensaje = {"accion": comandoAccion}
                if nombreAccion:
                    Mensaje["nombre"] = nombreAccion
                if teclaAccion:
                    Mensaje["key"] = teclaAccion

                self.mensajeMonitorESP(Mensaje, "accion")

            try:
                return self.ListaAcciones[comandoAccion](opcionesAccion)
            except Exception as Error:
                logger.exception(f"Accion[Error-{comandoAccion}] {Error}")
        else:
            logger.info(f"Accion[No Encontrada] {comandoAccion}")

        return None

    def AccionesMacros(self, ListaComando):
        """
        Ejecuta acciones una por una de una lista y si existe data la pasa a la siquiente accion

        ListaComandos -> list
            Acciones a realizar
        """
        cajon = {}
        for numero, comando in enumerate(ListaComando):

            logger.info(f"Macro[{numero+1}/{len(ListaComando)}]")
            # print("Comando", comando)

            self.solisitaMacro(comando, cajon)

            respuesta = self.ejecutarAcción(comando)

            self.respuestaMacro(comando, respuesta, cajon)

        # TODO: Hacer Macros en diferentes Hilos

    def accionesPresionar(self, opciones: list[valoresAcciones]):

        precionado: dict = self.obtenerValor(opciones, "presionado")
        soltar: dict = self.obtenerValor(opciones, "soltar")
        estado: bool = self.obtenerValor(opciones, "estado")

        if estado:
            logger.info(f"AccionOOP[presionar] - Precionando")
            return self.ejecutarAcción(precionado)
        else:
            logger.info(f"AccionOOP[presionar] - Soltando")
            return self.ejecutarAcción(soltar)

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
                    self.ejecutarAcción(accion)

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
        return self.ejecutarAcción(Selecion)

    def Reiniciar(self, opciones):
        """
        Reinicia la data del programa.
        """
        logger.info("Reiniciar data ElGarrobo")

        nombreDispositivo: str = self.obtenerValor(opciones, "dispositivo")

        if nombreDispositivo is None:
            for dispositivo in self.listaDispositivos:
                dispositivo.recargarAccionesFolder()
                dispositivo.actualizar()
        else:
            for dispositivo in self.listaDispositivos:
                if dispositivo.nombre.lower() == nombreDispositivo.lower():
                    dispositivo.recargarAccionesFolder(directo=True)
                    dispositivo.actualizar()

    def regresar_Folder(self, opciones: list[valoresAcciones]):

        nombreDispositivo: str = self.obtenerValor(opciones, "dispositivo")
        seRegreso: bool = False

        if nombreDispositivo is None:
            for dispositivo in self.listaDispositivos:
                dispositivo.regresarFolderActual()
                if dispositivo.recargar:
                    seRegreso = True
                dispositivo.actualizar()
        else:
            for disposito in self.listaDispositivos:
                if disposito.nombre.lower() == nombreDispositivo.lower():
                    disposito.regresarFolderActual(directo=True)
                    dispositivo.actualizar()
                    if dispositivo.recargar:
                        seRegreso = True

        if not seRegreso:
            logger.info("No se puedo regresar")

    def entrar_Folder(self, opciones: list[valoresAcciones]):
        """
        Entra en folder
        """
        folder: str = self.obtenerValor(opciones, "folder")
        nombreDispositovo: str = self.obtenerValor(opciones, "dispositivo")

        seCargo: bool = False

        if folder is None:
            logger.warning(f"Folder[no encontrado]")
            return

        if nombreDispositovo is None:
            for dispositivo in self.listaDispositivos:
                dispositivo.cargarAccionesFolder(folder)
                if dispositivo.recargar:
                    seCargo = True
                dispositivo.actualizar()
        else:
            for dispositivo in self.listaDispositivos:
                if dispositivo.nombre.lower() == nombreDispositovo.lower():
                    dispositivo.cargarAccionesFolder(folder, directo=True)
                    dispositivo.actualizar()
                    if dispositivo.recargar:
                        seCargo = True

        if not seCargo:
            logger.info("No se puede cargar informacion nueva")

    def Actualizar_Folder(self, opciones: list[valoresAcciones]):
        self.ActualizarDeck()

    def siquiente_Pagina(self, opciones: list[valoresAcciones]):
        for dispositivo in self.listaDispositivos:
            if hasattr(dispositivo, "siguientePagina"):
                dispositivo.siguientePagina()
                dispositivo.actualizar()

    def anterior_Pagina(self, opciones: list[valoresAcciones]):
        for dispositivo in self.listaDispositivos:
            if hasattr(dispositivo, "anteriorPagina"):
                dispositivo.anteriorPagina()
                dispositivo.actualizar()

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

    def IniciarMQTT(self):
        """Iniciar coneccion con Broker MQTT."""
        self.ListaMQTT = []
        self.Data["mqtt"] = leerData("mqtt")
        # todo: no existe mqtt.json
        if "mqtt" in self.Data and self.Data["mqtt"] is not None:
            for DataMQTT in self.Data["mqtt"]:
                ServidorMQTT = MiMQTT(DataMQTT, self.ejecutarAcción)
                self.ListaMQTT.append(ServidorMQTT)
            for ServidorMQTT in self.ListaMQTT:
                ServidorMQTT.Conectar()

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
        self.Pulse.IniciarAcciones(self.ListaAcciones, self.listaClasesAcciones)

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
        logger.info("ElGarrobo[Saliendo] - Adios :) ")
        if self.ModuloOBS:
            self.OBS.desconectar()
        if self.ModuloMQTT:
            for Servidor in self.ListaMQTT:
                Servidor.Desconectar()
        for dispositivo in self.listaDispositivos:
            dispositivo.desconectar()
        # raise SystemExit
        os._exit(0)

    def SolisitarDibujar(self):

        self.ActualizarDeck()

    def SolisitarNotifiacacion(self, texto, opciones: dict[valoresAcciones]):
        if self.ModuloOBSNotificacion:
            objetoAccion: accion = self.listaClasesAcciones["notificacion"]()
            objetoAccion.configurar({"texto": texto})
            objetoAccion.ejecutar()

            if opciones is None:
                logger.error("error en configuracciones")
            else:
                opciones["mensaje"] = texto
                accionMQTT = self.listaClasesAcciones["mqtt"]()
                accionMQTT.configurar(opciones)
                accionMQTT.ejecutar()

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
