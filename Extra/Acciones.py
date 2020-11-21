from Extra.Depuracion import Imprimir


def AgregarStreanDeck(_Deck):
    global Deck
    Deck = _Deck


def RealizarAccion(Accion):
    global Deck

    # if 'Siquiente' in Accion:
    #     Deck.BotonesSiquiente(True)
    #     Deck.ActualizarTodasImagenes()
    # elif 'Anterior' in Accion:
    #     Deck.BotonesSiquiente(False)
    #     Deck.ActualizarTodasImagenes()
    if 'Regresar' in Accion:
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
    else:
        Imprimir("Boton - no definida")
