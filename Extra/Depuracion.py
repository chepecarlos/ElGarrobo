depura = True


def CambiarDepuracion(Estado):
    global depura
    depura = Estado


def Imprimir(Mensaje):
    '''Imprimi mensaje de depuracion'''
    global depura
    if(depura):
        print(Mensaje)
