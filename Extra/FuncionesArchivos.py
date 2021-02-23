import json
import os
import sys
import yaml

from Extra.Depuracion import Imprimir

ArchivoLocal = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def ActualizarDato(Archivo, Valor, Atributo):
    '''Actualiza Valor de un Atributo Archivo'''
    Archivo = ArchivoLocal + Archivo
    if os.path.exists(Archivo):
        with open(Archivo) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
    else:
        data = []

    data[Atributo] = Valor

    with open(Archivo, 'w') as f:
        json.dump(data, f, indent=4)


def ObtenerDato(Archivo, Atributo, local=True):
    '''Obtiene Atributo de un Archivo .json'''
    if local:
        Archivo = ArchivoLocal + Archivo
    if Archivo.endswith(".json"):
        if os.path.exists(Archivo):
            with open(Archivo) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        else:
            Imprimir(f"Archivo no Exite {Archivo}")
            return ""
    elif Archivo.endswith(".md"):
        with open(Archivo) as f:
            try:
                data = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]
            except yaml.YAMLError as exc:
                Imprimir(f"error con yaml {exc}")
                return ""

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
