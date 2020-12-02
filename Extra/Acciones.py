import sys

import Extra.MiOBS as MiOBSs

from Extra.Depuracion import Imprimir
from Extra.Delay import Delay
from Extra.MiOS import MiOS
from Extra.EmularTeclado import ComandoTeclas, ComandoEscribir
from Extra.FuncionesProyecto import AbirProyecto


def AgregarStreanDeck(_Deck):
    global Deck
    Deck = _Deck


def AgregarOBS(_MiOBS):
    global MiOBS
    MiOBS = _MiOBS


def RealizarAccion(Accion):
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
            RealizarAccion(AccionMacro)
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
        ActualizarOBS(Accion)
    elif 'Opcion' in Accion:
        if Accion['Opcion'] == "Exit":
            # TODO: ver si esta habierto antes de cerrar
            Imprimir("Saliendo ElGatoALSW - Adios :) ")
            sys.exit()
            # MiOBS.Cerrar()
            # MiMQTT.Cerrar()
            # MiDeck.reset()
            # MiDeck.close()
        else:
            Imprimir(f"Opcion No Encontrada: {Accion['Opcion']}")
    else:
        Imprimir("Boton - no definida")


def ActualizarOBS(Accion):
    global MiOBS
    global Deck
    '''Acciones que puede enviarse a OBS_WebSoket'''
    # print(Accion)
    if Accion['OBS'] == "Cerrar":
        MiOBS.DesregistarEvento(EventoOBS)
        MiOBS.Cerrar()
        return True
    elif Accion['OBS'] == "Server" and 'Server' in Accion:
        AgregarOBS(MiOBSs.MiObsWS(Deck.Carpeta))
        MiOBS.CambiarHost(Accion['Server'])
        MiOBS.Conectar()
        MiOBS.RegistarEvento(EventoOBS)
    else:
        AgregarOBS(MiOBSs.MiObsWS())
        MiOBS.CambiarHost(Accion['OBS'])
        MiOBS.Conectar()
        MiOBS.RegistarEvento(EventoOBS)
        return True
    return False


def EventoOBS(mensaje):
    '''Escucha y Reaciona a eventos de OBS'''
    global MiOBS
    global Deck
    IdOBS = Deck.BuscarCarpeta(MiOBS.Carpeta)
    if mensaje.name == "Exiting":
        try:
            print("Cerrando OBS")
            # MiOBS.DesregistarEvento(EventoOBS)
            MiOBS.Cerrar()
            MiOBS.OBSConectado = True
        except Exception as e:
            print(f"No se pudo conectar a OBS - {e}")
            MiOBS.OBSConectado = False
    elif mensaje.name == 'RecordingStopped':
        Imprimir('Parado la grabacion')
        # IdGrabar = BuscarBoton(IdOBS, 'Rec')
        # data['Comando'][IdOBS]['Key'][IdGrabar]['Estado'] = False
        # ActualizarImagenes()
    elif mensaje.name == 'RecordingStarted':
        Imprimir('Iniciado la grabacion')
        # IdGrabar = BuscarBoton(IdOBS, 'Rec')
        # data['Comando'][IdOBS]['Key'][IdGrabar]['Estado'] = True
        # ActualizarImagenes()
    elif(mensaje.name == 'StreamStopped'):
        Imprimir("Parando la trasmicion")
        # IdLive = BuscarBoton(IdOBS, 'Live')
        # data['Comando'][IdOBS]['Key'][IdLive]['Estado'] = False
        # ActualizarImagenes()
    elif(mensaje.name == 'StreamStarted'):
        Imprimir("Empezando la trasmicion")
        # IdLive = BuscarBoton(IdOBS, 'Live')
        # data['Comando'][IdOBS]['Key'][IdLive]['Estado'] = True
        # ActualizarImagenes()
    elif(mensaje.name == 'SwitchScenes'):
        Imprimir(f"Cambia a Esena {mensaje.datain['scene-name']}")
        # EsenaActiva = BuscarBoton(IdOBS, mensaje.datain['scene-name'])
        # for tecla in range(len(data['Comando'][IdOBS]['Key'])):
        #     if EsEsena(IdOBS, tecla):
        #         if(EsenaActiva == tecla):
        #             data['Comando'][IdOBS]['Key'][tecla]['Estado'] = True
        #         else:
        #             data['Comando'][IdOBS]['Key'][tecla]['Estado'] = False
        # ActualizarImagenes()
    elif(mensaje.name == 'SceneItemVisibilityChanged'):
        NombreIten = mensaje.datain['item-name']
        EstadoItem = mensaje.datain['item-visible']
        # IdItem = BuscarBoton(IdOBS, NombreIten)
        Imprimir(f"Se cambio fuente {NombreIten} - {EstadoItem}")
        # data['Comando'][IdOBS]['Key'][IdItem]['Estado'] = EstadoItem
        # ActualizarImagenes()
    elif(mensaje.name == 'SourceFilterVisibilityChanged'):
        NombreFiltro = mensaje.datain['filterName']
        NombreFuente = mensaje.datain['sourceName']
        EstadoFiltro = mensaje.datain['filterEnabled']
        Imprimir(f"Se cambio el filtro {NombreFiltro} de {NombreFuente} a {EstadoFiltro}")
        # IdItem = BuscarBoton(IdOBS, NombreFiltro)
        # data['Comando'][IdOBS]['Key'][IdItem]['Estado'] = EstadoFiltro
        # ActualizarImagenes()
    else:
        Imprimir(f"Evento no procesado de OBS: {mensaje.name}")
