import json
import os
import sys
import yaml

# TODO: Icono Link se Apaga cuando no hay LinkNoticia
# TODO: Contador de ID Noticia Actual / Total Noticias
# TODO: Macro Sonido de Siquiente Noticia
from Extra.Depuracion import Imprimir

ArchivoNoticias = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..")) + '/Data/News.json'
ArchivoID = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..")) + '/Data/IdNews.json'
ArchivoTituloNoticias = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..")) + '/Data/News/TituloNoticia.txt'
ArchivoTituloAutor = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..")) + '/Data/News/TituloAutor.txt'


def SalvarArchivoNoticia(Directorio):
    global Archivo
    data = {}
    data['Noticia'] = str(Directorio)
    Imprimir(f"El Archivo de Noticas es {data['Noticia']}")
    with open(ArchivoNoticias, 'w+') as file:
        json.dump(data, file, indent=4)
    AsignarNoticia(0)


def SalvarIdNoticia(ID):
    global Archivo
    data = {}
    data['ID'] = str(ID)
    with open(ArchivoID, 'w+') as file:
        json.dump(data, file, indent=4)


def SalvarTexto(Archivo, Texto):
    with open(Archivo, 'w+') as file:
        file.write(Texto)


def CargarArchivoNoticia():
    global ArchivoNoticias
    if os.path.exists(ArchivoNoticias):
        with open(ArchivoNoticias) as f:
            data = json.load(f)
            if 'Noticia' in data:
                return data['Noticia']
    else:
        Imprimir(f"No se Encontro el Archivo {ArchivoNoticias}")
        sys.exit()


def CargarIDNoticia():
    global ArchivoID
    if os.path.exists(ArchivoID):
        with open(ArchivoID) as f:
            data = json.load(f)
            if 'ID' in data:
                return int(data['ID'])
    else:
        Imprimir(f"No se Encontro el Archivo {ArchivoID}")
        sys.exit()


def CargarNoticias():
    Archivo = CargarArchivoNoticia()
    with open(Archivo) as f:
        try:
            data = list(yaml.load_all(f, Loader=yaml.SafeLoader))[
                0]['custom_sections']
            for i in range(len(data)):
                if 'title' in data[i]:
                    if data[i]['title'] == "Noticias":
                        return data[i]['items']
        except yaml.YAMLError as exc:
            print("error con yaml")
            return exc


def CambiarNoticia(Cambiar=True):
    global ArchivoTituloNoticias
    global ArchivoTituloAutor
    Noticias = CargarNoticias()
    ID = CargarIDNoticia()
    if Cambiar:
        ID += 1
    else:
        ID -= 1

    if ID < 0:
        ID = 0
    elif ID >= len(Noticias):
        ID = len(Noticias) - 1
    SalvarIdNoticia(ID)
    SalvarTexto(ArchivoTituloNoticias, Noticias[ID]['title'])
    if 'author' in Noticias[ID]:
        SalvarTexto(ArchivoTituloAutor, "Autor: " + Noticias[ID]['author']['name'])
    else:
        SalvarTexto(ArchivoTituloAutor, " ")


def AsignarNoticia(ID):
    global ArchivoTituloNoticias
    global ArchivoTituloAutor
    Noticias = CargarNoticias()
    SalvarIdNoticia(ID)
    SalvarTexto(ArchivoTituloNoticias, Noticias[ID]['title'])
    if 'author' in Noticias[ID]:
        SalvarTexto(ArchivoTituloAutor, "Autor: " + Noticias[ID]['author']['name'])
    else:
        SalvarTexto(ArchivoTituloAutor, " ")


def LinkNoticia():
    Noticias = CargarNoticias()
    ID = CargarIDNoticia()

    if 'url' in Noticias[ID]:
        return Noticias[ID]['url']
    else:
        return "No Link"
