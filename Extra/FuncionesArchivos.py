import json
import os
import sys
import yaml

from Extra.Depuracion import Imprimir

ArchivoLocal = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def ActualizarDato(Archivo, Valor, Atributo):
    '''Actualiza Valor de un Atributo Archivo Json'''
    Archivo = ArchivoLocal + Archivo
    if os.path.exists(Archivo):
        with open(Archivo) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
    else:
        data = []

    data[Atributo] = Valor

    with open(Archivo, 'w') as f:
        json.dump(data, f, indent=4)


def ObtenerDato(Archivo, Atributo):
    '''Obtiene Atributo de un Archivo .json'''
    Archivo = ArchivoLocal + Archivo
    if os.path.exists(Archivo):
        with open(Archivo) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
    if Atributo in data:
        return data[Atributo]
    else:
        return ""


def ObtenerLista(Archivo, Atributo, ID):
    Lista = ObtenerDato(Archivo, Atributo)
    print(len(Lista))
    if ID < 0 or ID >= len(Lista):
        return "No Lista"
    return Lista[ID]
