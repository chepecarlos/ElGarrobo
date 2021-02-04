import os
import multiprocessing
import simpleaudio as sa
from Extra.Depuracion import Imprimir

ListaSonidos = []


def Sonido(Archivo):
    try:
        sound = sa.WaveObject.from_wave_file(Archivo)
        Repoductor = sound.play()
        print(f"Empezar a repoducir {Archivo}")
        Repoductor.wait_done()
        print(f"Terminando de repoducir {Archivo}")
    except FileNotFoundError:
        print(f"No se encontro {Archivo}")


def Reproducir(Archivo):
    global ListaSonidos
    Imprimir(f"Repoduciendo {Archivo}")
    Archivo = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..')) + "/" + Archivo
    PSonido = multiprocessing.Process(target=Sonido, args=[Archivo])
    PSonido.start()
    ListaSonidos.append(PSonido)


def PararReproducion():
    global ListaSonidos
    Imprimir("Parar Reproducion de Sonidos")
    for Sonido in ListaSonidos:
        Sonido.terminate()
