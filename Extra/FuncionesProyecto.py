import json
import os
import sys
import yaml

from Extra.Depuracion import Imprimir

ArchivoLocal = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
Archivo = ArchivoLocal + '/Data/Proyecto.json'


def SalvarProyecto(Directorio):
    global Archivo
    data = {}
    data['ProyectoActual'] = str(Directorio)

    with open(Archivo, 'w') as file:
        json.dump(data, file, indent=4)


def CargarProyecto():
    global Archivo
    if os.path.exists(Archivo):
        with open(Archivo) as f:
            data = json.load(f)
            if 'ProyectoActual' in data:
                return data['ProyectoActual']
    else:
        Imprimir(f"No se Encontro el Archivo {Archivo}")
        sys.exit()


def CargarIdVideo():
    Archivo = CargarProyecto() + "/1.Guion/1.Info.md"
    with open(Archivo) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        if 'youtube_id' in data:
            return data['youtube_id']


def AbirProyecto(Opcion):
    FolderProyecto = CargarProyecto()
    if Opcion == '':
        Comando = "nemo " + FolderProyecto + " &"
    else:
        Comando = "nemo " + FolderProyecto + "/" + Opcion + " &"
    Imprimir(Comando)
    os.system(Comando)


def GuardadDato(Archivo, Valor):
    if os.path.exists(Archivo):
        with open(Archivo) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
    else:
        data = []
    data.append(Valor)

    with open(Archivo, 'w') as f:
        json.dump(data, f, indent=4)


def ActualizarDato(Archivo, Valor, Atributo):
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
    Archivo = ArchivoLocal + Archivo
    if os.path.exists(Archivo):
        with open(Archivo) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
    if Atributo in data:
        return data[Atributo]
    else:
        return ""


def CrearFolderProyecto(NombreFolder):
    Imprimir(f"{NombreFolder}")
