import sys

import Extra.MiOBS as MiOBSs

from Extra.Depuracion import Imprimir
from Extra.Delay import Delay
from Extra.MiOS import MiOS
from Extra.EmularTeclado import ComandoTeclas, ComandoEscribir
from Extra.FuncionesProyecto import AbirProyecto
from Extra.News import CambiarNoticia, AsignarNoticia


def AgregarStreanDeck(_Deck):
    global Deck
    Deck = _Deck


def AgregarOBS(_MiOBS):
    global MiOBS
    MiOBS = _MiOBS


def Accion(Accion):
    global Deck

    # No Saltar extra
    if 'Siquiente' in Accion:
        Deck.BotonesSiquiente(True)
        Deck.ActualizarTodasImagenes(True)
    elif 'Anterior' in Accion:
        Deck.BotonesSiquiente(False)
        Deck.ActualizarTodasImagenes(True)
    elif 'Regresar' in Accion:
        Deck.BotonActuales = Deck.Data['Comando']
        # ComandosRaton = data['teclado']
        Deck.DesfaceBoton = 0
        Deck.Carpeta = "Base"
        Deck.ActualizarTodasImagenes()
    elif 'Key' in Accion:
        Imprimir("Entenado en folder")
        Deck.BotonActuales = Accion['Key']
        Deck.DesfaceBoton = 0
        Deck.Carpeta = Accion['Nombre']
        # if 'teclado' in accion:
        #     Imprimir("Cargando Teclado")
        #     ComandosRaton = accion['teclado']
        Deck.ActualizarTodasImagenes(True)
    elif 'Macro' in Accion:
        for AccionMacro in Accion['Macro']:
            Accion(AccionMacro)
    elif 'os' in Accion:
        MiOS(Accion['os'])
    elif 'tecla' in Accion:
        ComandoTeclas(Accion['tecla'])
    elif 'texto' in Accion:
        ComandoEscribir(Accion['texto'])
    elif 'delay' in Accion:
        Delay(Accion['delay'])
    elif 'Proyecto' in Accion:
        AbirProyecto(Accion['Proyecto'])
    elif 'OBS' in Accion:
        AccionesOBS(Accion)
    elif "StreamDeck" in Accion:
        AccionesStreanDeck(Accion)
    elif 'MQTT' in Accion:
        Imprimir("Cosas de MQTT")
    elif 'News' in Accion:
        AccionesNews(Accion)
        # MiMQTT.CambiarHost(accion['MQTT'])
        # MiMQTT.Conectar()
    # elif 'mqtt' in accion:
    #     Imprimir(f"Comando MQTT {accion['mqtt']}")
    #     MiMQTT.Enviando(accion['mqtt'])
    elif 'Opcion' in Accion:
        if Accion['Opcion'] == "Exit":
            # TODO: ver si esta habierto antes de cerrar
            Imprimir("Saliendo ElGatoALSW - Adios :) ")
            CerrarOBS()
            sys.exit()
            # MiMQTT.Cerrar()
            # MiDeck.reset()
            # MiDeck.close()
        else:
            Imprimir(f"Opcion No Encontrada: {Accion['Opcion']}")
    else:
        Imprimir("Boton - no definida")


def AccionesStreanDeck(Accion):
    global Deck
    if Accion['StreamDeck'] == "SubirBrillo":
        Deck.CambiarBrillo(5)
    elif Accion['StreamDeck'] == "BajarBrillo":
        Deck.CambiarBrillo(-5)


def AccionesOBS(Accion):
    '''Acciones que puede enviarse a OBS_WebSoket'''
    global MiOBS
    global Deck
    if Accion['OBS'] == "Server" and 'Server' in Accion:
        AgregarOBS(MiOBSs.MiObsWS(Deck.Carpeta))
        MiOBS.CambiarHost(Accion['Server'])
        MiOBS.Conectar()
        MiOBS.RegistarEvento(EventoOBS)
        Deck.OBSConectado = True
    elif Deck.OBSConectado:
        if Accion['OBS'] == "Cerrar":
            CerrarOBS()
        elif Accion['OBS'] == "Grabar":
            MiOBS.CambiarGrabacion()
        elif Accion['OBS'] == "Live":
            MiOBS.CambiarStriming()
        elif Accion['OBS'] == "Esena":
            MiOBS.CambiarEsena(Accion['Esena'])
        elif Accion['OBS'] == "Fuente":
            MiOBS.CambiarFuente(Accion['Fuente'], not Accion['Estado'])
        elif Accion['OBS'] == "Filtro":
            MiOBS.CambiarFiltro(Accion['Fuente'], Accion['Filtro'], not Accion['Estado'])
        else:
            Imprimir("No encontramos esta Opcion de OBS")
    else:
        Imprimir("OBS no Conectado")


def CerrarOBS():
    global MiOBS
    global Deck
    if Deck.OBSConectado:
        Deck.OBSConectado = False
        MiOBS.DesregistarEvento(EventoOBS)
        MiOBS.Cerrar()


def EventoOBS(Mensaje):
    '''Escucha y Reaciona a eventos de OBS'''
    global MiOBS
    global Deck
    IdOBS = Deck.BuscarCarpeta(MiOBS.Carpeta)
    if Mensaje.name == "Exiting":
        try:
            print("Cerrando OBS - Evento")
            CerrarOBS()
        except Exception as e:
            print(f"No se pudo conectar a OBS - {e}")
            MiOBS.OBSConectado = False
    elif Mensaje.name == 'RecordingStopped':
        Imprimir(f'Parado la grabacion - {MiOBS.Carpeta}')
        IdGrabar = Deck.BuscarBoton(IdOBS, 'Rec')
        if IdGrabar != -1:
            Deck.CambiarEstadoBoton(IdOBS, IdGrabar, False)
            Deck.ActualizarTodasImagenes()
    elif Mensaje.name == 'RecordingStarted':
        Imprimir(f'Iniciado la grabacion - {MiOBS.Carpeta}')
        IdGrabar = Deck.BuscarBoton(IdOBS, 'Rec')
        if IdGrabar != -1:
            Deck.CambiarEstadoBoton(IdOBS, IdGrabar, True)
            Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'StreamStopped'):
        Imprimir("Parando la trasmicion")
        IdLive = Deck.BuscarBoton(IdOBS, 'Live')
        if IdLive != -1:
            Deck.CambiarEstadoBoton(IdOBS, IdLive, False)
            Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'StreamStarted'):
        Imprimir("Empezando la trasmicion")
        IdLive = Deck.BuscarBoton(IdOBS, 'Live')
        if IdLive != -1:
            Deck.CambiarEstadoBoton(IdOBS, IdLive, True)
            Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'SwitchScenes'):
        Imprimir(f"Cambia a Esena - {Mensaje.datain['scene-name']}")
        IdEsena = Deck.BuscarBoton(IdOBS, Mensaje.datain['scene-name'])
        for Boton in range(len(Deck.Data['Comando'][IdOBS]['Key'])):
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
        Imprimir(f"Se cambio fuente {NombreIten} - {EstadoItem}")
        Deck.CambiarEstadoBoton(IdOBS, IdItem, EstadoItem)
        Deck.ActualizarTodasImagenes()
    elif(Mensaje.name == 'SourceFilterVisibilityChanged'):
        NombreFiltro = Mensaje.datain['filterName']
        NombreFuente = Mensaje.datain['sourceName']
        EstadoFiltro = Mensaje.datain['filterEnabled']
        Imprimir(f"Se cambio el filtro {NombreFiltro} de {NombreFuente} a {EstadoFiltro}")
        IdItem = Deck.BuscarBoton(IdOBS, NombreFiltro)
        Deck.CambiarEstadoBoton(IdOBS, IdItem, EstadoFiltro)
        Deck.ActualizarTodasImagenes()
    else:
        Imprimir(f"Evento no procesado de OBS: {Mensaje.name}")


def AccionesNews(Accion):
    if Accion['News'] == "Siquiente":
        Imprimir("Siquiente Noticia")
        CambiarNoticia()
    elif Accion['News'] == "Anterior":
        Imprimir("Anterior Noticia")
        CambiarNoticia(False)
    elif Accion['News'] == "Reiniciar":
        Imprimir("Reiniciar Noticia")
        AsignarNoticia(0)
