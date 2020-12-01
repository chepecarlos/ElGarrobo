import sys

from Extra.Depuracion import Imprimir
from Extra.Delay import Delay
from Extra.MiOS import MiOS
from Extra.EmularTeclado import ComandoTeclas, ComandoEscribir
from Extra.FuncionesProyecto import AbirProyecto


def AgregarStreanDeck(_Deck):
    global Deck
    Deck = _Deck


def RealizarAccion(Accion):
    global Deck

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
