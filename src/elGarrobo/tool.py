import argparse
import re
from pathlib import Path

from elGarrobo.miLibrerias import ConfigurarLogging, EscribirArchivo, ObtenerArchivo

logger = ConfigurarLogging(__name__)


def ordenarNatural(texto: str) -> list:
    """Convierte un string en lista para ordenación natural.

    Ejemplo: 'item10' -> ['item', 10, '']
    Permite ordenar 'item1', 'item2', 'item10' correctamente

    Args:
        texto (str): texto a procesar

    Returns:
        list: lista con partes para comparación
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", str(texto))]


def parametros() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="Heramientas extras de elGarrobo")
    parser.add_argument("--ordenar", "-o", help="Ordena el archivo .md")
    parser.add_argument("--convertir", "-c", help="Convertir de .json a .md")
    parser.add_argument("--depuracion", "-d", help="Activa la depuración", action="store_true")

    return parser.parse_args()


def convertirArchivo(archivo: str) -> None:
    """Convierte .json en .md

    Args:
        archivo (str): nombre del archivo .json a convertir
    """

    tipo: str = Path(archivo).suffix
    nombre: str = archivo.removesuffix(tipo)

    if tipo != ".json":
        logger.error("No es archivo .json")
        return

    if not Path(archivo).exists():
        logger.error(f"El archivo {archivo} no existe")
        return

    try:
        data = ObtenerArchivo(archivo, EnConfig=False)
    except Exception as e:
        logger.error(f"Error al leer archivo {archivo}: {e}")
        return

    if not data:
        logger.warning("El archivo está vacío")
        return

    try:
        EscribirArchivo(f"{nombre}.md", data)
        logger.info(f"Archivo convertido: {archivo} → {nombre}.md")
    except Exception as e:
        logger.error(f"Error al escribir archivo {nombre}.md: {e}")


def ordenarArchivo(archivo: str) -> None:
    """Ordena archivo .md en base a key

    Args:
        archivo (str): nombre del archivo .md a ordenar
    """

    tipo: str = Path(archivo).suffix

    if tipo != ".md":
        logger.error("No es archivo .md")
        return

    try:
        data = ObtenerArchivo(archivo, EnConfig=False)
    except Exception as e:
        logger.error(f"Error al leer archivo {archivo}: {e}")
        return

    if not data:
        logger.warning("El archivo está vacío")
        return

    keysVistos = set()
    for i, valor in enumerate(data):
        if not isinstance(valor, dict):
            logger.error(f"Elemento {i} no es un diccionario")
            return

        keyActual = valor.get("key")
        if not keyActual:
            logger.error(f"Elemento {i} no tiene clave 'key'")
            return

        if keyActual in keysVistos:
            logger.error(f"Se repite el key '{keyActual}'")
            return

        keysVistos.add(keyActual)

    data.sort(key=lambda x: ordenarNatural(x.get("key")), reverse=False)
    EscribirArchivo(archivo, data)
    logger.info(f"Archivo {archivo} ordenado correctamente ({len(data)} elementos)")


def main() -> None:

    args = parametros()

    if args.ordenar:
        ordenarArchivo(args.ordenar)
    elif args.convertir:
        convertirArchivo(args.convertir)


if __name__ == "__main__":
    main()
