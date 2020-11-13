import json
import os

Archivo =  os.path.abspath(os.path.join(os.path.dirname(__file__),"..")) + '/Recursos/Data.json'

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

def AbirProyecto(Opcion):
    FolderProyecto = CargarProyecto()
    if Opcion == '':
        Comando = "nemo " + FolderProyecto
    else:
        Comando = "nemo " + FolderProyecto + "/" + Opcion
    os.system(Comando)
