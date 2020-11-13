depura = True

def CambiarDepuracion(Estado):
    global depura
    depura = Estado

def Imprimir(dato):
    '''Imprimi mensaje de depuracion'''
    global depura
    if(depura):
        print(dato)
