import os
import Extra.MiOBS as MiOBSs
import logging

from Extra.MiOS import MiOS
from Extra.FuncionesProyecto import AbirProyecto
from Extra.FuncionesArchivos import ObtenerDato, ActualizarDato, ObtenerLista
from Extra.News import CambiarNoticia, AsignarNoticia, LinkNoticia
from Extra.Sonidos import Reproducir, PararReproducion
from Extra.MiMQTT import EnviarMQTTSimple
from libreria.FuncionesLogging import ConfigurarLogging

from libreria.acciones.EmularTeclado import ComandoTeclas, ComandoEscribir, PegarTexto, CopiarTexto
from libreria.acciones.Delay import Delay

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


def AccionesExtra(AccionActual):
    # global Deck

    # No Saltar extra

    # Moviendo a liberia
    # TODO Ordenar por importancia
    if 'tecla' in AccionActual:
        ComandoTeclas(AccionActual['tecla'])
    elif 'texto' in AccionActual:
        ComandoEscribir(AccionActual['texto'])
    elif 'delay' in AccionActual:
        Delay(AccionActual['delay'])
    elif 'macro' in AccionActual:
        for AccionMacro in AccionActual['Macro']:
            AccionesExtra(AccionMacro)
            # TODO Codigo roto para macro

    # Viejas acciones
    elif 'streamDeck' in AccionActual:
        logger.info("Entenado en folder")
        Deck.BotonActuales = AccionActual['streamDeck']
        Deck.DesfaceBoton = 0
        Deck.Carpeta = AccionActual['nombre']
        Deck.ConfigurandoTeclados(AccionActual['nombre'])
        # if 'teclado' in accion:
        #     Imprimir("Cargando Teclado")
        #     ComandosRaton = accion['teclado']
        Deck.ActualizarTodasImagenes(True)

    elif 'os' in AccionActual:
        MiOS(AccionActual['os'])


    elif 'Proyecto' in AccionActual:
        AbirProyecto(AccionActual['Proyecto'])
    elif 'OBS' in AccionActual:
        AccionesOBS(AccionActual)
    elif "configdeck" in AccionActual:
        AccionesStreanDeck(AccionActual)
    elif 'mqtt' in AccionActual:
        AccionesMQTT(AccionActual)
    elif 'news' in AccionActual:
        AccionesNews(AccionActual)
    elif 'sonido' in AccionActual:
        AccionSonido(AccionActual)
    elif 'archivo' in AccionActual:
        AccionesArchivos(AccionActual)

    else:
        logger.warning(f"Boton - no definida {AccionActual['nombre']}")


def AccionSonido(AccionActual):
    if AccionActual['Sonido'] == 'Parar':
        PararReproducion()
    else:
        Reproducir(AccionActual['Sonido'])


def AccionesStreanDeck(AccionActual):
    global Deck
    if AccionActual['ConfigDeck'] == "SubirBrillo":
        Deck.CambiarBrillo(5)
    elif AccionActual['ConfigDeck'] == "BajarBrillo":
        Deck.CambiarBrillo(-5)


def AccionesMQTT(AccionActual):
    if AccionActual['mqtt'] == "mensaje" and 'topic' in AccionActual and 'mensaje' in AccionActual:
        logger.info(f"Enviando Mensaje MQTT {AccionActual['topic']} - {AccionActual['mensaje']}")
        EnviarMQTTSimple(AccionActual['topic'], AccionActual['mensaje'])


def AccionesOBS(AccionActual):
    '''Acciones que puede enviarse a OBS_WebSoket'''
    global MiOBS
    global Deck
    if AccionActual['obs'] == "Server" and 'Server' in AccionActual:
        AgregarOBS(MiOBSs.MiObsWS(Deck.Carpeta))
        MiOBS.CambiarHost(AccionActual['Server'])
        MiOBS.Conectar()
        MiOBS.RegistarEvento(EventoOBS2)
        Deck.OBSConectado = True
    elif Deck.OBSConectado:
        if AccionActual['obs'] == "Cerrar":
            CerrarOBS()
        elif AccionActual['obs'] == "Grabar":
            MiOBS.CambiarGrabacion()
        elif AccionActual['obs'] == "Live":
            MiOBS.CambiarStriming()
        elif AccionActual['obs'] == "Esena":
            MiOBS.CambiarEsena(AccionActual['Esena'])
        elif AccionActual['obs'] == "Fuente":
            MiOBS.CambiarFuente(AccionActual['Fuente'], not AccionActual['Estado'])
        elif AccionActual['obs'] == "Filtro":
            MiOBS.CambiarFiltro(AccionActual['Fuente'], AccionActual['Filtro'], not AccionActual['Estado'])
        else:
            logger.warning("No encontramos esta Opcion de OBS")
    else:
        logger.warning("OBS no Conectado")


def CerrarOBS():
    global MiOBS
    global Deck
    if Deck.OBSConectado:
        Deck.OBSConectado = False
        MiOBS.DesregistarEvento(EventoOBS2)
        MiOBS.Cerrar()


def EventoOBS2(Mensaje):
    '''Mensajes de OBS '''
    global Deck
    # TODO: Buscar Esena Actual al conectarse al Servidor de OBS
    # TODO: Eliminar funciones CambiarEstadoBoton
    # Imprimir(f"Evento OBS {Mensaje}")
    if(Mensaje.name == 'SwitchScenes'):
        logger.info(f"Cambiando a Esena OBS - {Mensaje.datain['scene-name']}")
        ActualizarDato("/Data/OBS.json", Mensaje.datain['scene-name'], "EsenaActual")
        Deck.ActualizarTodasImagenes()
    elif Mensaje.name == 'RecordingStopped':
        logger.info('Parado la grabacion en OBS')
        ActualizarDato("/Data/OBS.json", False, "EstadoGrabando")
        Deck.ActualizarTodasImagenes()
    elif Mensaje.name == 'RecordingStarted':
        logger.info('Iniciado la grabacion en OBS ')
        ActualizarDato("/Data/OBS.json", True, "EstadoGrabando")
        Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'StreamStopped'):
        logger.info("Parando la trasmicion")
        ActualizarDato("/Data/OBS.json", False, "EstadoLive")
    elif(Mensaje.name == 'StreamStarted'):
        logger.info("Empezando la trasmicion")
        ActualizarDato("/Data/OBS.json", True, "EstadoLive")
    elif(Mensaje.name == 'SceneItemVisibilityChanged'):
        NombreIten = Mensaje.datain['item-name']
        EstadoItem = Mensaje.datain['item-visible']
        logger.info(f"Se cambio fuente {NombreIten} - {EstadoItem}")
        # TODO: Guardas Estado de Fuente
        Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'SourceFilterVisibilityChanged'):
        NombreFiltro = Mensaje.datain['filterName']
        NombreFuente = Mensaje.datain['sourceName']
        EstadoFiltro = Mensaje.datain['filterEnabled']
        logger.info(f"Se cambio el filtro {NombreFiltro} de {NombreFuente} a {EstadoFiltro}")
        # Todo: Guardas Estado del Filtro
        Deck.ActualizarTodasImagenes()
    else:
        logger.warning(f"Evento no procesado de OBS: {Mensaje.name}")


def EventoOBS(Mensaje):
    '''Escucha y Reaciona a eventos de OBS'''
    logger.info(Mensaje.name)
    global MiOBS
    global Deck
    IdOBS = Deck.BuscarCarpeta(MiOBS.Carpeta)
    if Mensaje.name == "Exiting":
        try:
            logger.info("Cerrando OBS - Evento")
            CerrarOBS()
        except Exception as e:
            logger.warning(f"No se pudo conectar a OBS - {e}")
            MiOBS.OBSConectado = False
    elif Mensaje.name == 'RecordingStopped':
        logger.info(f'Parado la grabacion - {MiOBS.Carpeta}')
        IdGrabar = Deck.BuscarBoton(IdOBS, 'Rec')
        if IdGrabar != -1:
            Deck.CambiarEstadoBoton(IdOBS, IdGrabar, False)
            Deck.ActualizarTodasImagenes()
    elif Mensaje.name == 'RecordingStarted':
        logger.info(f'Iniciado la grabacion - {MiOBS.Carpeta}')
        IdGrabar = Deck.BuscarBoton(IdOBS, 'Rec')
        if IdGrabar != -1:
            Deck.CambiarEstadoBoton(IdOBS, IdGrabar, True)
            Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'StreamStopped'):
        logger.info("Parando la trasmicion")
        IdLive = Deck.BuscarBoton(IdOBS, 'Live')
        if IdLive != -1:
            Deck.CambiarEstadoBoton(IdOBS, IdLive, False)
            Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'StreamStarted'):
        logger.info("Empezando la trasmicion")
        IdLive = Deck.BuscarBoton(IdOBS, 'Live')
        if IdLive != -1:
            Deck.CambiarEstadoBoton(IdOBS, IdLive, True)
            Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'SwitchScenes'):
        logger.info(f"Cambia a Esena - {Mensaje.datain['scene-name']}")
        IdEsena = Deck.BuscarBoton(IdOBS, Mensaje.datain['scene-name'])
        for Boton in range(len(Deck.Data['StreamDeck'][IdOBS]['StreamDeck'])):
            if Deck.EsEsena(IdOBS, Boton):
                if IdEsena == Boton:
                    Deck.CambiarEstadoBoton(IdOBS, Boton, True)
                else:
                    Deck.CambiarEstadoBoton(IdOBS, Boton, False)
        Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'SceneItemVisibilityChanged'):
        NombreIten = Mensaje.datain['item-name']
        EstadoItem = Mensaje.datain['item-visible']
        IdItem = Deck.BuscarBoton(IdOBS, NombreIten)
        logger.info(f"Se cambio fuente {NombreIten} - {EstadoItem}")
        Deck.CambiarEstadoBoton(IdOBS, IdItem, EstadoItem)
        Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'SourceFilterVisibilityChanged'):
        NombreFiltro = Mensaje.datain['filterName']
        NombreFuente = Mensaje.datain['sourceName']
        EstadoFiltro = Mensaje.datain['filterEnabled']
        logger.info(f"Se cambio el filtro {NombreFiltro} de {NombreFuente} a {EstadoFiltro}")
        IdItem = Deck.BuscarBoton(IdOBS, NombreFiltro)
        Deck.CambiarEstadoBoton(IdOBS, IdItem, EstadoFiltro)
        Deck.ActualizarTodasImagenes()
    else:
        logger.warning(f"Evento no procesado de OBS: {Mensaje.name}")


def AccionesNews(AccionActual):
    if AccionActual['News'] == "Siquiente":
        logger.info("Siquiente Noticia")
        CambiarNoticia()
    elif AccionActual['News'] == "Anterior":
        logger.info("Anterior Noticia")
        CambiarNoticia(False)
    elif AccionActual['News'] == "Reiniciar":
        logger.info("Reiniciar Noticia")
        AsignarNoticia(0)
    elif AccionActual['News'] == "Link":
        logger.info("Pegar Link de Noticia")
        Link = LinkNoticia()
        ComandoEscribir(Link)
    else:
        logger.warning("No accion de News")


def AccionesArchivos(AccionActual):
    if AccionActual['Archivo'] == "Reiniciar":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            logger.info(f"Reiniciando {AccionActual['Atributo']}")
            ActualizarDato("/Data/" + AccionActual['json'], 0, AccionActual['Atributo'])
    if AccionActual['Archivo'] == "Siquiente":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            CantidadActual = ObtenerDato("/Data/" + AccionActual['json'], AccionActual['Atributo']) + 1
            logger.info(f"Incrementando {AccionActual['Atributo']} a {CantidadActual}")
            ActualizarDato("/Data/" + AccionActual['json'], CantidadActual, AccionActual['Atributo'])
    if AccionActual['Archivo'] == "Anterior":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            CantidadActual = ObtenerDato("/Data/" + AccionActual['json'], AccionActual['Atributo']) - 1
            logger.info(f"Bajando {AccionActual['Atributo']} a {CantidadActual}")
            ActualizarDato("/Data/" + AccionActual['json'], CantidadActual, AccionActual['Atributo'])
    if AccionActual['Archivo'] == "Lista":
        if 'json' in AccionActual and 'Lista' in AccionActual and 'ID' in AccionActual:
            CantidadActual = ObtenerDato("/Data/" + AccionActual['json'], AccionActual['ID'])
            Texto = ObtenerLista("/Data/" + AccionActual['json'], AccionActual['Lista'], CantidadActual)
            logger.info(f"Posicion {CantidadActual} - {Texto}")
            ComandoEscribir(Texto)
    if AccionActual['Archivo'] == "Pegar":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            Texto = ObtenerDato("/Data/" + AccionActual['json'], AccionActual['Atributo'])
            PegarTexto(Texto)
    elif AccionActual['Archivo'] == "Salvar":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            Texto = CopiarTexto()
            ActualizarDato("/Data/" + AccionActual['json'], Texto, AccionActual['Atributo'])
