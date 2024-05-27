
import argparse
from pathlib import Path

from elGarrobo.miLibrerias import ConfigurarLogging
from elGarrobo.miLibrerias import ObtenerArchivo, EscribirArchivo

logger = ConfigurarLogging(__name__)

def Parametros():

    parser = argparse.ArgumentParser(description="Heramientas extras de elGarrobo")
    parser.add_argument("--ordenar", "-o", help="Ordena el archivo .md")

    return parser.parse_args()


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
    EscribirArchivo(archivo, data)
    logger.info("Archivo ordenado")
    # TODO: decir si se ordeno o no

def main():
    
    args = Parametros()

    if args.ordenar:
        ordenarArchivo(args.ordenar)
    pass

if __name__ == "__main__":
    main()
