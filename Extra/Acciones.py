import sys

import Extra.MiOBS as MiOBSs

from Extra.Depuracion import Imprimir
from Extra.Delay import Delay
from Extra.MiOS import MiOS
from Extra.EmularTeclado import ComandoTeclas, ComandoEscribir
from Extra.FuncionesProyecto import AbirProyecto
from Extra.MiOBS import EventoOBS


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
        Deck.ActualizarTodasImagenes()
    elif 'Key' in Accion:
        Imprimir("Entenado en folder")
        Deck.BotonActuales = Accion['Key']
        Deck.DesfaceBoton = 0
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
    '''Acciones que puede enviarse a OBS_WebSoket'''
    # print(Accion)
    if Accion['OBS'] == "Cerrar":
        MiOBS.DesregistarEvento(EventoOBS)
        MiOBS.Cerrar()
        return True
    elif Accion['OBS'] == "Server" and 'Server' in Accion:
        AgregarOBS(MiOBSs.MiObsWS())
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
