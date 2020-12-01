import os
import json
import sys
from Extra.Depuracion import Imprimir


def CargarData(Direcion):
    """Carga Archivo de comandos y Raton"""
    Data = CargarValores(Direcion)
    if 'CargandoRaton' in Data:
        Data['teclado'] = CargarValores(Data['CargandoRaton'])
    if 'CargandoComando' in Data:
        Data['Comando'] = CargarValores(Data['CargandoComando'])
    for i in range(len(Data['Comando'])):
        if 'Cargar' in Data['Comando'][i]:
            Data['Comando'][i]['Key'] = CargarValores(Data['Comando'][i]['Cargar'])
        if 'CargandoRaton' in Data['Comando'][i]:
            Data['Comando'][i]['teclado'] = CargarValores(Data['Comando'][i]['CargandoRaton'])
    return AgregarComodines(Data)
    return Data


def CargarValores(Direcion):
    """Cargando Data de un Archivo"""
    archivo = os.path.join(os.path.dirname(__file__), '..') + "/" + Direcion
    if os.path.exists(archivo):
        with open(archivo) as f:
            return json.load(f)
    else:
        Imprimir(f"No se Encontro el Archivo: {archivo}")
        sys.exit()


def AgregarComodines(Data):
    # Agregando al final Regresar
    if 'Comando' in Data:
        Data['Comando'].append({
          "Nombre": "Regresar",
          "Regresar": True
        })
        for Boton in range(len(Data['Comando'])):
            if 'Nombre' in Data['Comando'][Boton]:
                # Imprimir(Data['Comando'][Boton]['Nombre'])
                if 'Key' in Data['Comando'][Boton]:
                    # Imprimir(Data['Comando'][Boton]['Key'])
                    Data['Comando'][Boton]['Key'].append({
                      "Nombre": "Regresar",
                      "Regresar": True
                    })
    return Data
