from Extra.MiCharBot import EnviarMensaje
from Extra.Depuracion import Imprimir
from Extra.SubProceso import EmpezarSubProceso
import time
import datetime


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
    print(Archivo)
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
