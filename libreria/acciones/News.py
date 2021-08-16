import os

# TODO: Contador de ID Noticia Actual / Total Noticias
# TODO: Macro Sonido de Siquiente Noticia

from libreria.FuncionesArchivos import SalvarValor, SalvarArchivo, ObtenerValor, UnirPath

import MiLibrerias

logger = MiLibrerias.ConfigurarLogging(__name__)


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
        if 'url' in Noticias[ID]:
            return Noticias[ID]['url']
    return None


def BuscarEnNoticia(Atributo):
    Archivo = ObtenerValor("data/news.json", "archivo")
    ID = ObtenerValor("data/news.json", "id")
    Noticias = ObtenerValor(Archivo, "news")

    if ID <= len(Noticias):
        if Atributo in Noticias[ID]:
            return Noticias[ID][Atributo]
    return None


def ActualizarNoticias():
    SalvarValor("data/news.json", "max", CantidadNoticias())
    LinkActual = BuscarEnNoticia('url')
    if LinkActual is None:
        SalvarValor("data/estado.json", "LinkNews", False)
    else:
        print(LinkActual)
        SalvarValor("data/estado.json", "LinkNews", True)
    TituloActual = BuscarEnNoticia('title')
    ArchivoNews = ObtenerValor("data/news.json", "titulo_news")
    if TituloActual is not None and ArchivoNews is not None:
        SalvarArchivo(ArchivoNews, TituloActual)
    AuthorActual = BuscarEnNoticia('author')
    ArchivoAuthor = ObtenerValor("data/news.json", "author_news")
    if AuthorActual is not None and ArchivoAuthor is not None and 'name' in AuthorActual:
        SalvarArchivo(ArchivoAuthor, AuthorActual['name'])
    else:
        SalvarArchivo(ArchivoAuthor, "")
