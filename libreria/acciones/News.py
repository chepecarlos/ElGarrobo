import os
import logging

# TODO: Contador de ID Noticia Actual / Total Noticias
# TODO: Macro Sonido de Siquiente Noticia

from libreria.FuncionesArchivos import SalvarValor, ObtenerValor, UnirPath
from libreria.FuncionesLogging import ConfigurarLogging

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


def SalvarArchivoNoticia(Archivo):
    Archivo = UnirPath(os.getcwd(), Archivo)
    logger.info(f"Actualiznado Archivo Noticia - {Archivo}")
    SalvarValor("data/news.json", "archivo", Archivo)
    SalvarValor("data/news.json", "id", 0)
    SalvarValor("data/news.json", "max", CantidadNoticias())


def CantidadNoticias():
    Archivo = ObtenerValor("data/news.json", "archivo")
    Noticias = ObtenerValor(Archivo, "news")
    return len(Noticias) - 1


def LinkNoticia():
    Archivo = ObtenerValor("data/news.json", "archivo")
    ID = ObtenerValor("data/news.json", "id")
    Noticias = ObtenerValor(Archivo, "news")

    if ID <= len(Noticias):
        print(ID, Noticias[ID])
        if 'url' in Noticias[ID]:
            return Noticias[ID]['url']
    return None
