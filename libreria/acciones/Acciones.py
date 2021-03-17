import os
import logging

from Extra.MiOS import MiOS
from Extra.FuncionesProyecto import AbirProyecto
from Extra.FuncionesArchivos import ObtenerDato, ActualizarDato, ObtenerLista
from Extra.News import CambiarNoticia, AsignarNoticia, LinkNoticia
from libreria.FuncionesLogging import ConfigurarLogging

from libreria.acciones.MiMQTT import EnviarMQTTSimple
from libreria.acciones.Sonidos import AccionSonido
from libreria.acciones.EmularTeclado import ComandoTeclas, ComandoEscribir, PegarTexto, CopiarTexto
from libreria.acciones.Delay import Delay

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)


def AccionesExtra(AccionActual):
    # Moviendo a liberia
    # TODO Ordenar por importancia
    if 'tecla' in AccionActual:
        ComandoTeclas(AccionActual['tecla'])
    elif 'texto' in AccionActual:
        ComandoEscribir(AccionActual['texto'])
    elif 'delay' in AccionActual:
        Delay(AccionActual['delay'])
    elif 'macro' in AccionActual:
        for AccionMacro in AccionActual['Macro']:
            AccionesExtra(AccionMacro)
            # TODO Codigo roto para macro
    elif 'sonido' in AccionActual:
        AccionSonido(AccionActual)
    elif 'mqtt' in AccionActual:
        AccionesMQTT(AccionActual)

    # TODO cosas viejas
    elif 'os' in AccionActual:
        MiOS(AccionActual['os'])
    elif 'Proyecto' in AccionActual:
        AbirProyecto(AccionActual['Proyecto'])
    elif 'news' in AccionActual:
        AccionesNews(AccionActual)

    elif 'archivo' in AccionActual:
        AccionesArchivos(AccionActual)

    else:
        logger.warning(f"Boton - no definida {AccionActual['nombre']}")


def AccionesMQTT(AccionActual):
    if AccionActual['mqtt'] == "mensaje" and 'topic' in AccionActual and 'mensaje' in AccionActual:
        logger.info(f"Enviando Mensaje MQTT {AccionActual['topic']} - {AccionActual['mensaje']}")
        EnviarMQTTSimple(AccionActual['topic'], AccionActual['mensaje'])


def AccionesNews(AccionActual):
    if AccionActual['News'] == "Siquiente":
        logger.info("Siquiente Noticia")
        CambiarNoticia()
    elif AccionActual['News'] == "Anterior":
        logger.info("Anterior Noticia")
        CambiarNoticia(False)
    elif AccionActual['News'] == "Reiniciar":
        logger.info("Reiniciar Noticia")
        AsignarNoticia(0)
    elif AccionActual['News'] == "Link":
        logger.info("Pegar Link de Noticia")
        Link = LinkNoticia()
        ComandoEscribir(Link)
    else:
        logger.warning("No accion de News")


def AccionesArchivos(AccionActual):
    if AccionActual['Archivo'] == "Reiniciar":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            logger.info(f"Reiniciando {AccionActual['Atributo']}")
            ActualizarDato("/Data/" + AccionActual['json'], 0, AccionActual['Atributo'])
    if AccionActual['Archivo'] == "Siquiente":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            CantidadActual = ObtenerDato("/Data/" + AccionActual['json'], AccionActual['Atributo']) + 1
            logger.info(f"Incrementando {AccionActual['Atributo']} a {CantidadActual}")
            ActualizarDato("/Data/" + AccionActual['json'], CantidadActual, AccionActual['Atributo'])
    if AccionActual['Archivo'] == "Anterior":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            CantidadActual = ObtenerDato("/Data/" + AccionActual['json'], AccionActual['Atributo']) - 1
            logger.info(f"Bajando {AccionActual['Atributo']} a {CantidadActual}")
            ActualizarDato("/Data/" + AccionActual['json'], CantidadActual, AccionActual['Atributo'])
    if AccionActual['Archivo'] == "Lista":
        if 'json' in AccionActual and 'Lista' in AccionActual and 'ID' in AccionActual:
            CantidadActual = ObtenerDato("/Data/" + AccionActual['json'], AccionActual['ID'])
            Texto = ObtenerLista("/Data/" + AccionActual['json'], AccionActual['Lista'], CantidadActual)
            logger.info(f"Posicion {CantidadActual} - {Texto}")
            ComandoEscribir(Texto)
    if AccionActual['Archivo'] == "Pegar":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            Texto = ObtenerDato("/Data/" + AccionActual['json'], AccionActual['Atributo'])
            PegarTexto(Texto)
    elif AccionActual['Archivo'] == "Salvar":
        if 'json' in AccionActual and 'Atributo' in AccionActual:
            Texto = CopiarTexto()
            ActualizarDato("/Data/" + AccionActual['json'], Texto, AccionActual['Atributo'])
