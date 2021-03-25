import logging

# from Extra.MiOS import MiOS
from Extra.FuncionesProyecto import AbirProyecto
from Extra.FuncionesArchivos import ObtenerDato, ActualizarDato, ObtenerLista
from Extra.News import CambiarNoticia, AsignarNoticia, LinkNoticia

from libreria.FuncionesLogging import ConfigurarLogging
from libreria.acciones.MiOS import AccionOS
from libreria.acciones.MiMQTT import EnviarMQTTSimple
from libreria.acciones.Sonidos import AccionSonido
from libreria.acciones.EmularTeclado import ComandoTeclas, ComandoEscribir, PegarTexto, CopiarTexto
from libreria.acciones.Delay import Delay
from libreria.acciones.Data_Archivo import AccionDataArchivo

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


def AccionesExtra(accion):
    # Moviendo a liberia
    # TODO Ordenar por importancia
    if 'tecla' in accion:
        ComandoTeclas(accion['tecla'])
    elif 'texto' in accion:
        ComandoEscribir(accion['texto'])
    elif 'delay' in accion:
        Delay(accion['delay'])
    elif 'sonido' in accion:
        AccionSonido(accion)
    elif 'mqtt' in accion:
        AccionesMQTT(accion)
    elif 'os' in accion:
        AccionOS(accion['os'])
    elif 'data_archivo' in accion:
        print("probando ")
        AccionDataArchivo(accion)
    # TODO cosas viejas

    elif 'Proyecto' in accion:
        AbirProyecto(accion['Proyecto'])
    elif 'news' in accion:
        AccionesNews(accion)

    elif 'archivo' in accion:
        AccionesArchivos(accion)

    else:
        logger.warning(f"Boton - no definida {accion['nombre']}")


def AccionesMQTT(accion):
    if accion['mqtt'] == "mensaje" and 'topic' in accion and 'mensaje' in accion:
        logger.info(f"Enviando Mensaje MQTT {accion['topic']} - {accion['mensaje']}")
        EnviarMQTTSimple(accion['topic'], accion['mensaje'])


def AccionesNews(accion):
    if accion['News'] == "Siquiente":
        logger.info("Siquiente Noticia")
        CambiarNoticia()
    elif accion['News'] == "Anterior":
        logger.info("Anterior Noticia")
        CambiarNoticia(False)
    elif accion['News'] == "Reiniciar":
        logger.info("Reiniciar Noticia")
        AsignarNoticia(0)
    elif accion['News'] == "Link":
        logger.info("Pegar Link de Noticia")
        Link = LinkNoticia()
        ComandoEscribir(Link)
    else:
        logger.warning("No accion de News")


def AccionesArchivos(accion):
    if accion['Archivo'] == "Reiniciar":
        if 'json' in accion and 'Atributo' in accion:
            logger.info(f"Reiniciando {accion['Atributo']}")
            ActualizarDato("/Data/" + accion['json'], 0, accion['Atributo'])
    if accion['Archivo'] == "Siquiente":
        if 'json' in accion and 'Atributo' in accion:
            CantidadActual = ObtenerDato("/Data/" + accion['json'], accion['Atributo']) + 1
            logger.info(f"Incrementando {accion['Atributo']} a {CantidadActual}")
            ActualizarDato("/Data/" + accion['json'], CantidadActual, accion['Atributo'])
    if accion['Archivo'] == "Anterior":
        if 'json' in accion and 'Atributo' in accion:
            CantidadActual = ObtenerDato("/Data/" + accion['json'], accion['Atributo']) - 1
            logger.info(f"Bajando {accion['Atributo']} a {CantidadActual}")
            ActualizarDato("/Data/" + accion['json'], CantidadActual, accion['Atributo'])
    if accion['Archivo'] == "Lista":
        if 'json' in accion and 'Lista' in accion and 'ID' in accion:
            CantidadActual = ObtenerDato("/Data/" + accion['json'], accion['ID'])
            Texto = ObtenerLista("/Data/" + accion['json'], accion['Lista'], CantidadActual)
            logger.info(f"Posicion {CantidadActual} - {Texto}")
            ComandoEscribir(Texto)
    if accion['Archivo'] == "Pegar":
        if 'json' in accion and 'Atributo' in accion:
            Texto = ObtenerDato("/Data/" + accion['json'], accion['Atributo'])
            PegarTexto(Texto)
    elif accion['Archivo'] == "Salvar":
        if 'json' in accion and 'Atributo' in accion:
            Texto = CopiarTexto()
            ActualizarDato("/Data/" + accion['json'], Texto, accion['Atributo'])
