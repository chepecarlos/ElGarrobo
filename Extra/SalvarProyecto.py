import json
import os

def SalvarProyecto(Directorio):
    Archivo = os.path.abspath(os.path.join(os.path.dirname(__file__),"..")) + '/Recursos/Data.json'
    data = {}
    data['ProyectoActual'] = str(Directorio)

    with open(Archivo, 'w') as file:
        json.dump(data, file, indent=4)
