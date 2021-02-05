from Extra.MiCharBot import EnviarMensaje
from Extra.Depuracion import Imprimir


def CrearProxy(Directorio):
    EnviarMensaje(30085334, ("Empezar a crear <b>Proxy</b> " + Directorio))
    print(Directorio)


def RenderizarVideo(Archivo):
    EnviarMensaje(30085334, ("Empezar a <b>Rendizar Video</b> " + Archivo))
    print(Archivo)
