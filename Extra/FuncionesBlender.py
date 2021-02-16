from Extra.MiCharBot import EnviarMensaje
from Extra.Depuracion import Imprimir
from Extra.SubProceso import EmpezarSubProceso
import time
import datetime
import os
import shutil


def CrearProxy(Directorio):
    global IDChat
    EnviarMensaje("<b>Empezar</b> a crear Proxy" + Directorio)

    Inicio = time.time()
    comando = ['bpsproxy']
    EstadoPreceso = EmpezarSubProceso(comando)

    Final = time.time()
    Tiempo = round(Final - Inicio)
    Tiempo = str(datetime.timedelta(seconds=Tiempo))
    if EstadoPreceso == 0:
        Imprimir(f"Finalizo creacion de proxy {Tiempo} {Directorio}")
        EnviarMensaje("<b>Finalizo</b> creacion de proxy " + Tiempo + " - " + Directorio)
    else:
        Imprimir(f"ERROR {EstadoPreceso} creacion de proxy {Tiempo} {Directorio} ")
        EnviarMensaje("<b>ERROR</b> " + EstadoPreceso + "creacion de proxy" + Tiempo + " - " + Directorio)


def RenderizarVideo(Archivo):
    global IDChat
    EnviarMensaje("Empezar a <b>Rendizar Video</b> " + Archivo)
    Imprimir(Archivo)
    Inicio = time.time()
    comando = ['bpsrender', Archivo]
    EstadoPreceso = EmpezarSubProceso(comando)

    Final = time.time()
    Tiempo = round(Final - Inicio)
    Tiempo = str(datetime.timedelta(seconds=Tiempo))
    if EstadoPreceso == 0:
        Imprimir(f"Finalizo la renderizacion {Tiempo} {Archivo}")
        EnviarMensaje("<b>Finalizo</b> la renderizacion " + Tiempo + " - " + Archivo)
    else:
        Imprimir(f"ERROR {EstadoPreceso} la renderizacion {Tiempo} {Archivo} ")
        EnviarMensaje("<b>ERROR</b> " + EstadoPreceso + "la renderizacion" + Tiempo + " - " + Archivo)


def BorrarTemporalesBender(Directorio):
    # TODO: no entrar en folder ocultos
    Imprimir(f"Emezando a borrar {Directorio}")

    Ruta_Actual = os.getcwd()
    num_directorios = 0
    linea = '-' * 60

    for ruta, directorios, archivos in os.walk(Ruta_Actual, topdown=True):
        for directorio in directorios:
            if(directorio == Directorio):
                num_directorios += 1
                Imprimir(f"Borrar {ruta} {directorio}")
                shutil.rmtree(os.path.join(ruta, directorio))
    Imprimir(linea)
    Imprimir(f'Cantidad de folder {Directorio} eliminados: {num_directorios}')
