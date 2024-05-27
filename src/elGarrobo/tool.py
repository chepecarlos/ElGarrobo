
import argparse
from pathlib import Path

from elGarrobo.miLibrerias import ConfigurarLogging
from elGarrobo.miLibrerias import ObtenerArchivo, EscribirArchivo

logger = ConfigurarLogging(__name__)

def Parametros():

    parser = argparse.ArgumentParser(description="Heramientas extras de elGarrobo")
    parser.add_argument("--ordenar", "-o", help="Ordena el archivo .md")
    parser.add_argument("--convertir", "-c", help="Convertir de .json a .md")
    

    return parser.parse_args()

def convertirArchivo(archivo: str) -> None:
    
    tipo = Path(archivo).suffix
    nombre = archivo.removesuffix(tipo)
    
    if tipo != ".json":
        logger.error("No es archivo .json")
        return

    data = ObtenerArchivo(archivo, EnConfig=False)
    EscribirArchivo(f"{nombre}.md",data)


def ordenarArchivo(archivo: str) -> None:
    """Ordena archivo .md en base a key

    Args:
        archivo (str): nombre del archivo .md a ordenar 
    """

    tipo = Path(archivo).suffix
    
    if tipo != ".md":
        logger.error("No es archivo .md")
        return
        
    data = ObtenerArchivo(archivo, EnConfig=False)
    listaKey = []
    for valor in data:
        keyActual = valor.get("key")
        if keyActual in listaKey:
            print(f"Se repite el key {keyActual}")
            for búsqueda in data:
                if búsqueda.get("key") == keyActual:
                    print(búsqueda)
            return
        listaKey.append(keyActual)
     
    data.sort(key=lambda x: x.get("key"), reverse=False)
    
    dataOrdenada = []
    for valor in data:
        valorTMP = dict()
        valorTMP["nombre"] = valor.pop("nombre", "SinNombre")
        if "titulo" in valor:
            valorTMP["titulo"] = valor.pop("titulo")
        valorTMP["key"] = valor.pop("key")
        valorTMP["accion"] = valor.pop("accion")
        if "opciones" in valor:
            valorTMP["opciones"] =valor.pop("opciones")
        valorTMP |=  valor
        dataOrdenada.append(valorTMP)
        
    EscribirArchivo(archivo, dataOrdenada)
    logger.info("Archivo ordenado")
    # TODO: decir si se ordeno o no

def main():
    
    args = Parametros()

    if args.ordenar:
        ordenarArchivo(args.ordenar)
    elif args.convertir:
        convertirArchivo(args.convertir)
        

if __name__ == "__main__":
    main()
