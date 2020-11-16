import os
import json
import sys
from Extra.Depuracion import Imprimir

def CargarData(Direcion):
    """Carga Archivo de comandos"""
    Data = CargarValores(Direcion)
    if 'CargarData' in Data:
        Data['teclado'] = CargarValores(Data['CargandoRaton'])
    if 'CargandoComando' in Data:
        Data['Comando'] = CargarValores(Data['CargandoComando'])
        for i in range(len(Data['Comando'])):
            if 'Cargar' in Data['Comando'][i]:
                Data['Comando'][i]['Key'] = CargarValores(Data['Comando'][i]['Cargar'])
            if 'CargandoRaton' in Data['Comando'][i]:
                Data['Comando'][i]['teclado'] = CargarValores(Data['Comando'][i]['CargandoRaton'])
            print(Data['Comando'][i])
    return Data

def CargarValores(Direcion):
    archivo = os.path.join(os.path.dirname(__file__), '..') + "/" + Direcion
    if os.path.exists(archivo):
        with open(archivo) as f:
            return json.load(f)
    else:
        Imprimir(f"No se Encontro el Archivo: {archivo}")
        sys.exit()
