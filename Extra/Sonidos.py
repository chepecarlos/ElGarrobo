import os
import subprocess
import multiprocessing
from Extra.Depuracion import Imprimir

ListaSonidos = []


def Sonido(Archivo):
    subprocess.run(['play', Archivo], capture_output=True)


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
    Imprimir("Parar Reproducion")
    for Sonido in ListaSonidos:
        Sonido.terminate()
