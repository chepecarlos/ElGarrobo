import json
import os
import yaml
import logging

from pathlib import Path

from libreria.FuncionesLogging import ConfigurarLogging

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)

ArchivoLocal = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ArchivoConfiguracion = os.path.join(Path.home(), '.config/elgatoalsw')


def ActualizarDato(Archivo, Valor, Atributo):
    '''Actualiza Valor de un Atributo Archivo'''
    Archivo = ArchivoLocal + Archivo
    if os.path.exists(Archivo):
        with open(Archivo) as f:
            data = json.load(f)
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
            logger.warning(f"Archivo no Exite {Archivo}")
            return ""
    elif Archivo.endswith(".md"):
        with open(Archivo) as f:
            try:
                data = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]
            except yaml.YAMLError as exc:
                logger.warning(f"error con yaml {exc}")
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


def ObtenerConfig():
    return ArchivoConfiguracion


def ObtenerArchivo(Archivo):
    """Leer y devuelte la informacion de un archivo"""
    global ArchivoConfiguracion
    if Archivo.endswith(".json"):
        ArchivoActual = ArchivoConfiguracion + "/" + Archivo
        if os.path.exists(ArchivoActual):
            with open(ArchivoActual) as f:
                return yaml.load(f, Loader=yaml.FullLoader)
        else:
            logger.warning(f"No Eciste {Archivo}")
    else:
        logger.warning(f"El Archivo {Archivo} no es .json")


def ObtenerFolder(Directorio):
    """Devuelve una lista de los folder dentro de Directorio"""
    global ArchivoConfiguracion
    FolderActual = os.path.join(ArchivoConfiguracion, Directorio)
    ListaFolder = []
    if os.path.exists(FolderActual):
        for folder in os.listdir(FolderActual):
            if os.path.isdir(os.path.join(FolderActual, folder)):
                # ListaFolder.append({"folder": folder})
                ListaFolder.append(folder)
        return ListaFolder


def ObtenerArhivos(Directorio):
    global ArchivoConfiguracion
    FolderActual = os.path.join(ArchivoConfiguracion, Directorio)
    ListaArchivos = []
    if os.path.exists(FolderActual):
        for archivo in os.listdir(FolderActual):
            if os.path.isfile(os.path.join(FolderActual, archivo)):
                ListaArchivos.append(archivo)
        return ListaArchivos


def ObtenerValor(Archivo, Atributo, local=True):
    """Obtiene Atributo de un Archivo .json"""
    if local:
        Archivo = os.path.join(ArchivoConfiguracion, Archivo)
    if Archivo.endswith(".json"):
        if os.path.exists(Archivo):
            with open(Archivo) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        else:
            logger.warning(f"Archivo no Exite {Archivo}")
            return ""
    elif Archivo.endswith(".md"):
        with open(Archivo) as f:
            try:
                data = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]
            except yaml.YAMLError as exc:
                logger.warning(f"error con yaml {exc}")
                return ""

    if Atributo in data:
        return data[Atributo]
    else:
        logger.worning(f"No existe el atributo {Atributo}")
        return ""


def SalvarValor(Archivo, Atributo, Valor, local=True):
    data = dict()
    if local:
        Archivo = os.path.join(ArchivoConfiguracion, Archivo)
    if Archivo.endswith(".json"):
        if os.path.exists(Archivo):
            with open(Archivo) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        else:
            logger.warning(f"Archivo no Exite {Archivo}")
    elif Archivo.endswith(".md"):
        with open(Archivo) as f:
            try:
                data = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]
            except yaml.YAMLError as exc:
                logger.warning(f"error con yaml {exc}")

    data[Atributo] = Valor

    with open(Archivo, 'w') as f:
        json.dump(data, f, indent=2)


def SalvarArchivo(Archivo, Data):
    Archivo = os.path.join(ArchivoConfiguracion, Archivo)
    with open(Archivo, 'w') as f:
        json.dump(Data, f, indent=1)


def UnirPath(Path1, Path2):
    return os.path.join(Path1, Path2)
