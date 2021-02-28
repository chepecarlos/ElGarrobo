import os
import json
import sys
from Extra.Depuracion import Imprimir


def CargarData(Direcion):
    global Recursos
    """Carga Archivo de comandos y Raton"""
    Data = CargarValores(Direcion)
    if 'Configuraciones' in Data:
        Recursos = Data['Configuraciones'] + "/"
    else:
        Recursos = "Recursos/"
    if 'StreamDeck_file' in Data:
        Data['StreamDeck'] = CargarValores(Recursos + Data['StreamDeck_file'])
    if 'StreamDeck' in Data:
        for Folder in Data['StreamDeck']:
            if 'Folder' in Folder:
                Folder['StreamDeck'] = CargarValores(Recursos + Folder['Nombre'] + "/" + Data['StreamDeck_file'])
    if 'Teclados_file' in Data:
        Data['Teclados'] = CargarValores(Recursos + Data['Teclados_file'])
    if 'Deck_file' in Data:
        Data['Deck'] = CargarValores(Recursos + Data['Deck_file'])
    # if 'CargandoRaton' in Data:
    #     Data['teclado'] = CargarValores(Data['CargandoRaton'])
    # if 'CargandoComando' in Data:
    #     Data['Comando'] = CargarValores(Data['CargandoComando'])
    # for i in range(len(Data['Comando'])):
    #     if 'Cargar' in Data['Comando'][i]:
    #         Data['Comando'][i]['Key'] = CargarValores(Data['Comando'][i]['Cargar'])
    #     if 'CargandoRaton' in Data['Comando'][i]:
    #         Data['Comando'][i]['teclado'] = CargarValores(Data['Comando'][i]['CargandoRaton'])
    # print(Data['Teclados'])
    return Data


def CargarValores(Direcion, EnRecursos=False):
    """Cargando Data de un Archivo"""
    global Recursos
    if EnRecursos:
        archivo = os.path.join(os.path.dirname(__file__), '..') + "/" + Recursos + Direcion
    else:
        archivo = os.path.join(os.path.dirname(__file__), '..') + "/" + Direcion
    if os.path.exists(archivo):
        with open(archivo) as f:
            return json.load(f)
    else:
        Imprimir(f"No se Encontro el Archivo: {archivo}")
        sys.exit()


def ExisteArchivo(Direcion, EnRecursos=False, deputar=False):
    global Recursos
    if EnRecursos:
        archivo = os.path.join(os.path.dirname(__file__), '..') + "/" + Recursos + Direcion
    else:
        archivo = os.path.join(os.path.dirname(__file__), '..') + "/" + Direcion
    if deputar:
        Imprimir(archivo)
    if os.path.exists(archivo):
        return True
    return False


def AgregarComodines(Data, CantidaBotones):
    Data.append({
      "Nombre": "Regresar",
      "Regresar": True
    })
    for Boton in range(len(Data)):
        if 'StreamDeck' in Data[Boton]:
            AgregarComodines(Data[Boton]['StreamDeck'], CantidaBotones)

    i = 1
    Insertar = i * CantidaBotones
    while len(Data) > Insertar:
        if i != 1:
            Data.insert(Insertar - 2, {
                "Nombre": "Anterior",
                "Anterior": True
                })
        Data.insert(Insertar - 1, {
              "Nombre": "Siquiente",
              "Siquiente": True
            })
        i += 1
        Insertar = i * CantidaBotones
    if i != 1:
        Data.insert(len(Data) - 1, {
              "Nombre": "Anterior",
              "Anterior": True
            })
