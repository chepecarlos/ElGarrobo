#!/usr/bin/env python3
# TODO: agregar git https://python-elgato-streamdeck.readthedocs.io/en/stable/examples/animated.html
# TODO: Reordenar codigo
# BUG: Error cargando sin folder
# Librerias
import os
import sys
import threading
import time

# Librerias de ElGato
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
# Librerias para idenficiar Teclado
from evdev import InputDevice, categorize, ecodes
import argparse

import Extra.FuncionesOBS as OBSWebSocketPropios
import Extra.MiMQTT as MiMQTTs

# Cargar funciones de Archivos
from Extra.FuncionesProyecto import SalvarProyecto, CargarProyecto, AbirProyecto, CargarIdVideo
from Extra.EmularTeclado import ComandoTeclas, ComandoEscribir
from Extra.Depuracion import Imprimir, CambiarDepuracion
from Extra.YoutubeChat import SalvarChatYoutube
from Extra.CargarData import CargarData

# TODO: ordenar para no usar variable globales
MiDeck = "nada"
teclas = "nada"
ComandosRaton = "nada"
folder = ""
fuente = ""
data = ""
DefaceBotones = 0

MiOBS = OBSWebSocketPropios.MiObsWS()
MiMQTT = MiMQTTs.MiMQTT()
# TODO: Agregar sonidos
parser = argparse.ArgumentParser(description='Heramienta de creacion de contenido de ALSW')
parser.add_argument('--master', '-m', help="Cargar servidor de %(prog)s",  action="store_true")
parser.add_argument('--cliente', '-c', help="Cargando cliente de %(prog)s",  action="store_true")
parser.add_argument('--deck', '-d', help="Solo usar StreamDeck",  action="store_true")
parser.add_argument('--ratom', '-r', help="Solo usar Ratom Razer",  action="store_true")
parser.add_argument('--nodepurar', '-nd', help="Acivar modo sin depuracion", action="store_true")
parser.add_argument('--proyecto', '-p', help="Configurar folder a proyecto actual", action="store_true")
parser.add_argument('--salvaryoutube', '-sy', help="Salva el chat en un archivo", action="store_true")


def ActualizarImagen(deck, teclas, tecla, limpiar=False):
    global folder
    global DefaceBotones

    # TODO: Mejor logica de deface
    if(tecla + DefaceBotones < 0 or tecla + DefaceBotones > deck.key_count()):
        return

    image = PILHelper.create_image(deck)
    if not limpiar:
        titulo = ''
        if 'Titulo' in teclas[tecla]:
            titulo = "{}".format(teclas[tecla]['Titulo'])

        if 'Regresar' in teclas[tecla]:
            if 'ico' in teclas[tecla]:
                NombreIcon = "{}".format(teclas[tecla]['ico'])
            elif 'ico_Regresar' in data:
                NombreIcon = data['ico_Regresar']
            else:
                NombreIcon = "imagen.png"
        elif 'Estado' in teclas[tecla]:
            if teclas[tecla]['Estado'] and 'icon_true' in teclas[tecla]:
                NombreIcon = teclas[tecla]['icon_true']
            elif not teclas[tecla]['Estado'] and 'icon_false' in teclas[tecla]:
                NombreIcon = teclas[tecla]['icon_false']
            elif 'ico_defecto' in data:
                NombreIcon = data['ico_defecto']
            else:
                NombreIcon = "imagen.png"
        elif 'ico' in teclas[tecla]:
            NombreIcon = "{}".format(teclas[tecla]['ico'])
        else:
            if 'ico_defecto' in data:
                NombreIcon = data['ico_defecto']
            else:
                NombreIcon = "imagen.png"
        NombreIcon = os.path.dirname(os.path.realpath(__file__)) + "/" + NombreIcon
        if os.path.exists(NombreIcon):
            icon = Image.open(NombreIcon).convert("RGBA")
            if not titulo == '':
                icon.thumbnail((image.width, image.height - 20), Image.LANCZOS)
            else:
                icon.thumbnail((image.width, image.height), Image.LANCZOS)
            icon_posicion = ((image.width - icon.width) // 2, 0)
            image.paste(icon, icon_posicion, icon)
        else:
            Imprimir(f"No se encontro imagen {NombreIcon}")
            icon = Image.new(mode="RGBA", size=(256, 256), color=(153, 153, 255))
            icon.thumbnail((image.width, image.height), Image.LANCZOS)
            icon_posicion = ((image.width - icon.width) // 2, 0)
            image.paste(icon, icon_posicion, icon)

        if not titulo == '':
            dibujo = ImageDraw.Draw(image)
            font = ImageFont.truetype(fuente, 14)
            label_w, label_h = dibujo.textsize(titulo, font=font)
            label_pos = ((image.width - label_w) // 2, image.height - 20)
            dibujo.text(label_pos, text=titulo, font=font, fill="white")

    deck.set_key_image(tecla + DefaceBotones, PILHelper.to_native_format(deck, image))


def ActualizarTeclas(deck, tecla, estado):
    global teclas
    tecla = tecla - DefaceBotones
    if estado:
        if tecla < len(teclas):
            Imprimir(f"Boton {tecla} - {teclas[tecla]['Nombre']}")
            ActualizarAccion(teclas[tecla])
        else:
            Imprimir(f"Boton {tecla} - no programada")


def BotonesSiquiente(Siquiente):
    global MiDeck
    global DefaceBotones
    if Siquiente:
        DefaceBotones -= MiDeck.key_count()
    else:
        DefaceBotones += MiDeck.key_count()


def ActualizarAccion(accion):
    '''Acciones que se puede hacer con teclas'''
    global teclas
    global raton
    global DefaceBotones
    global ComandosRaton
    global MiDeck
    if 'Regresar' in accion:
        teclas = data['Comando']
        ComandosRaton = data['teclado']
        DefaceBotones = 0
        BorrarActualizarImagenes()
    elif 'Macro' in accion:
        for AccionMatro in accion['Macro']:
            ActualizarAccion(AccionMatro)
    elif 'delay' in accion:
        time.sleep(accion['delay'] / 1000)
    elif 'Siquiente' in accion:
        BotonesSiquiente(True)
        BorrarActualizarImagenes()
    elif 'Anterior' in accion:
        BotonesSiquiente(False)
        BorrarActualizarImagenes()
    elif ActualizarOBS(accion):
        True
    elif 'OS' in accion:
        os.system(accion['OS'])
    elif 'mqtt' in accion:
        Imprimir(f"Comando MQTT {accion['mqtt']}")
        MiMQTT.Enviando(accion['mqtt'])
    elif 'tecla' in accion:
        ComandoTeclas(accion['tecla'])
    elif 'texto' in accion:
        ComandoEscribir(accion['texto'])
    elif 'MQTT' in accion:
        Imprimir(f"Intentando MQTT_Remoto {accion['MQTT']}")
        MiMQTT.CambiarHost(accion['MQTT'])
        MiMQTT.Conectar()
    elif 'Proyecto' in accion:
        AbirProyecto(accion['Proyecto'])
    elif 'Opcion' in accion:
        if accion['Opcion'] == "Exit":
            # TODO: ver si esta habierto antes de cerrar
            MiOBS.Cerrar()
            MiMQTT.Cerrar()
            MiDeck.reset()
            MiDeck.close()
            Imprimir("Saliendo ElGato ALSW - Adios :) ")
        else:
            Imprimir(f"Opcion No Encontrada: {accion['Opcion']}")
    elif 'Key' in accion:
        Imprimir("Entenado en folder")
        teclas = accion['Key']
        if 'teclado' in accion:
            Imprimir("Cargando Teclado")
            ComandosRaton = accion['teclado']
        BorrarActualizarImagenes()
    else:
        Imprimir("Boton - no definida")


def ActualizarOBS(accion):
    '''Acciones que puede enviarse a OBS_WebSoket'''
    if 'OBS' in accion:
        ConectarOBS(accion['OBS'])
    elif 'Grabar' in accion:
        MiOBS.CambiarGrabacion()
    elif 'Live' in accion:
        MiOBS.CambiarStriming()
    elif 'CambiarEsena' in accion:
        MiOBS.CambiarEsena(accion['CambiarEsena'])
    elif 'Fuente' in accion:
        if 'Filtro' in accion:
            MiOBS.CambiarFiltro(accion['Fuente'], accion['Filtro'], accion['Estado'])
        else:
            MiOBS.CambiarFuente(accion['Fuente'], not accion['Estado'])
    else:
        return False
    return True


def ActualizarImagenes():
    global MiDeck
    for indice in range(len(teclas)):
        ActualizarImagen(MiDeck, teclas, indice)


def BorrarActualizarImagenes():
    global MiDeck
    # TODO: Mejorar la logica de guardad en tiemporal
    global DefaceBotones
    Tmp = DefaceBotones
    DefaceBotones = 0
    for key in range(MiDeck.key_count()):
        ActualizarImagen(MiDeck, teclas, key, True)
    DefaceBotones = Tmp
    ActualizarImagenes()


def ConectarOBS(servidor):
    '''Se conecta con el servidor y registra eventos'''
    MiOBS.CambiarHost(servidor)
    MiOBS.Conectar()
    MiOBS.RegistarEvento(EventoOBS)


def EventoOBS(mensaje):
    '''Escucha y Reaciona a eventos de OBS'''
    global MiOBS
    IdOBS = BuscarCarpeta('OBS')
    if IdOBS == -1:
        Imprimir("Error no encontado Botones")
        return
    if(mensaje.name == 'RecordingStopped'):
        Imprimir('Parado la grabacion')
        IdGrabar = BuscarBoton(IdOBS, 'Rec')
        data['Comando'][IdOBS]['Key'][IdGrabar]['Estado'] = False
        ActualizarImagenes()
    elif(mensaje.name == 'RecordingStarted'):
        Imprimir('Iniciado la grabacion')
        IdGrabar = BuscarBoton(IdOBS, 'Rec')
        data['Comando'][IdOBS]['Key'][IdGrabar]['Estado'] = True
        ActualizarImagenes()
    elif(mensaje.name == 'StreamStopped'):
        Imprimir("Parando la trasmicion")
        IdLive = BuscarBoton(IdOBS, 'Live')
        data['Comando'][IdOBS]['Key'][IdLive]['Estado'] = False
        ActualizarImagenes()
    elif(mensaje.name == 'StreamStarted'):
        Imprimir("Empezando la trasmicion")
        IdLive = BuscarBoton(IdOBS, 'Live')
        data['Comando'][IdOBS]['Key'][IdLive]['Estado'] = True
        ActualizarImagenes()
    elif(mensaje.name == 'SwitchScenes'):
        Imprimir(f"Cambia a Esena {mensaje.datain['scene-name']}")
        EsenaActiva = BuscarBoton(IdOBS, mensaje.datain['scene-name'])
        for tecla in range(len(data['Comando'][IdOBS]['Key'])):
            if EsEsena(IdOBS, tecla):
                if(EsenaActiva == tecla):
                    data['Comando'][IdOBS]['Key'][tecla]['Estado'] = True
                else:
                    data['Comando'][IdOBS]['Key'][tecla]['Estado'] = False
        ActualizarImagenes()
    elif(mensaje.name == 'SceneItemVisibilityChanged'):
        NombreIten = mensaje.datain['item-name']
        EstadoItem = mensaje.datain['item-visible']
        IdItem = BuscarBoton(IdOBS, NombreIten)
        Imprimir(f"Se cambio fuente {NombreIten} - {EstadoItem}")
        data['Comando'][IdOBS]['Key'][IdItem]['Estado'] = EstadoItem
        ActualizarImagenes()
    elif(mensaje.name == 'SourceFilterVisibilityChanged'):
        NombreFiltro = mensaje.datain['filterName']
        NombreFuente = mensaje.datain['sourceName']
        EstadoFiltro = mensaje.datain['filterEnabled']
        Imprimir(f"Se cambio el filtro {NombreFiltro} de {NombreFuente} a {EstadoFiltro}")
        IdItem = BuscarBoton(IdOBS, NombreFiltro)
        data['Comando'][IdOBS]['Key'][IdItem]['Estado'] = EstadoFiltro
        ActualizarImagenes()
    elif(mensaje.name == 'Exiting'):
        Imprimir("Cerrando por OBS")
        # MiOBS = ''
        MiOBS.Cerrar()
    else:
        Imprimir(f"Evento no procesado de OBS: {mensaje}")


def BuscarCarpeta(nombre):
    for tecla in range(len(data['Comando'])):
        if(data['Comando'][tecla]['Nombre'] == nombre):
            return tecla
    return -1


def BuscarBoton(IdFolder, nombre):
    if(IdFolder == -1):
        return -1
    for tecla in range(len(data['Comando'][IdFolder]['Key'])):
        if(data['Comando'][IdFolder]['Key'][tecla]['Nombre'] == nombre):
            return tecla
    return -1


def EsEsena(IdFolder, IdEsena):
    if('CambiarEsena' in data['Comando'][IdFolder]['Key'][IdEsena]):
        return True
    return False


def BuscandoBoton(NombreFolder, NombreBoton):
    IdFolder = BuscarCarpeta(NombreFolder)
    return BuscarBoton(IdFolder, NombreBoton)


#  Codigo del Raton_Razer


def CargandoRaton():
    '''Cargas las configuraciones del Teclado Ratom'''
    global data
    global ComandosRaton
    Imprimir("Cargando Raton Razer")
    ComandosRaton = data['teclado']
    if 'Raton_Razer' in data:
        Raton = InputDevice(data['Raton_Razer'])
        Raton.grab()
        HiloRazer = threading.Thread(target=HiloRaton, args=(Raton,), daemon=True)
        HiloRazer.start()
    else:
        Imprimir("error Raron Razer no definido")


def HiloRaton(Raton):
    '''Hila del teclado del Raton'''
    global ComandosRaton
    for event in Raton.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            if key.keystate == key.key_down:
                for teclas in ComandosRaton:
                    if 'Boton' in teclas:
                        if teclas['Boton'] == key.keycode:
                            Imprimir(f"Raton {key.keycode} - {teclas['Nombre']}")
                            ActualizarAccion(teclas)


def CargandoElGato():
    '''Cargas StreamDeck'''
    global data
    global teclas
    global fuente
    global MiDeck
    # Buscando Dispisitovos
    streamdecks = DeviceManager().enumerate()

    Imprimir(f"Programa El Gato ALSW - {'Encontrado' if len(streamdecks) > 0 else 'No Conectado'}")

    for index, deck in enumerate(streamdecks):

        MiDeck = deck
        # Abriendo puerto
        deck.open()
        deck.reset()

        Imprimir(f"Abriendo '{deck.deck_type()}' dispositivo (Numero Serial: '{deck.get_serial_number()}')")

        # Cambiar Brillo
        if 'Brillo' in data:
            deck.set_brightness(data['Brillo'])
        else:
            deck.set_brightness(50)

        if 'Fuente' in data:
            fuente = os.path.dirname(os.path.realpath(__file__)) + "/" + data['Fuente']
        else:
            Imprimir("Fuente no asignada")
            deck.close()

        teclas = data['Comando']
        for tecla in range(len(teclas)):
            ActualizarImagen(deck, teclas, tecla)

        # Sistema de Coalbask
        deck.set_key_callback(ActualizarTeclas)


def CargarHilo():
    '''Carga los todos los hilos disponibles'''
    for t in threading.enumerate():
        if t is threading.currentThread():
            continue

        if t.is_alive():
            t.join()


# Principal
if __name__ == "__main__":
    args = parser.parse_args()
    if args.nodepurar:
        CambiarDepuracion(False)

    if args.master:
        Imprimir("Modo Master")
        data = CargarData('Comandos.json')
        CargandoRaton()
        CargandoElGato()
        CargarHilo()
    elif args.cliente:
        Imprimir("Modo Cliente")
    elif args.deck:
        Imprimir("Modo Solo StreamDeck")
        data = CargarData('Comandos.json')
        CargandoElGato()
        CargarHilo()
    elif args.ratom:
        Imprimir("Modo Solo Raton Razer")
        data = CargarData('Comandos.json')
        CargandoRaton()
        CargarHilo()
    elif args.proyecto:
        Imprimir("Configurando Folder como Proyecto Actual")
        SalvarProyecto(os.getcwd())
    elif args.salvaryoutube:
        Imprimir("Emezandoa a guardar Chat en Proyecto Actual")
        SalvarChatYoutube(CargarProyecto(), CargarIdVideo())
    else:
        Imprimir("No parametro")
        data = CargarData('Comandos.json')
        CargandoRaton()
        CargandoElGato()
        CargarHilo()
