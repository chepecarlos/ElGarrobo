import os
import pickle
import logging

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from Extra.FuncionesArchivos import ObtenerDato
from libreria.FuncionesLogging import ConfigurarLogging, NivelLogging

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)

ArchivoLocal = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def CargarCredenciales():
    '''Optienes credenciales para API de youtube'''
    credentials = None
    ArchivoPickle = ArchivoLocal + "/Data/token.pickle"
    if os.path.exists(ArchivoPickle):
        print('Cargando credenciales el Archivo pickle...')
        with open(ArchivoPickle, 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print('Recargando credenciales...')
            credentials.refresh(Request())
        else:
            print('Opteniendo nuevas credenciales...')
            client_secrets = ArchivoLocal + "/Data/client_secrets.json"
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets,
                scopes=[
                    'https://www.googleapis.com/auth/youtube.readonly',
                    'https://www.googleapis.com/auth/youtube',
                    'https://www.googleapis.com/auth/youtubepartner'
                ]
            )

            flow.run_local_server(port=8080, prompt='consent',
                                  authorization_prompt_message='')
            credentials = flow.credentials

            with open(ArchivoPickle, 'wb') as f:
                print('Salvando credenciales para el futuro en archivo pickle...')
                pickle.dump(credentials, f)

    return credentials


def ActualizarDescripcion(video_id, archivo=""):
    credenciales = CargarCredenciales()
    if archivo == "":
        ActualizarVideo(video_id, credenciales)
    else:
        ActualizarVideo(video_id, credenciales, archivo)


def ActualizarVideo(video_id, credenciales, archivo=""):
    DescripcionVideo = ""
    if not archivo:
        archivo = "Zen_" + video_id + ".txt"
        logger.info(f"Usando el archivo {archivo} por defecto")

    if os.path.exists(archivo):
        with open(archivo, 'r') as linea:
            DescripcionVideo = linea.read()
    else:
        logger.warning(f"Erro fatal el archivo {archivo} no existe")
        return
    youtube = build("youtube", "v3", credentials=credenciales)

    SolisitudVideo = youtube.videos().list(
        id=video_id,
        part='snippet'
      )

    DataVideo = SolisitudVideo.execute()
    if len(DataVideo["items"]) > 0:
        SnippetVideo = DataVideo["items"][0]["snippet"]

        if DescripcionVideo == SnippetVideo["description"]:
            logger.info("Ya Actualizado")
            return 0

        SnippetVideo["description"] = DescripcionVideo

        SolisituActualizar = youtube.videos().update(
            part='snippet',
            body=dict(
              snippet=SnippetVideo,
              id=video_id
            ))

        RespuestaYoutube = SolisituActualizar.execute()
        if len(RespuestaYoutube['snippet']) > 0:
            logger.info("Actualizacion Completa")
            return 1
        else:
            logger.warning("Hubo un problema?")
            return -1
    else:
        logger.warning(f"No existe el video con ID {video_id}")
        return -1


def ActualizarDescripcionFolder():
    credenciales = CargarCredenciales()
    contador = 0
    total = len(os.listdir("."))
    Actualizados = 0
    for archivo in os.listdir("."):
        if archivo.endswith(".txt"):
            contador += 1
            video_id = archivo.replace(".txt", "")
            logger.info(f"Verificando ({contador}/{total}) - Video_ID:{video_id}")
            Resultado = ActualizarVideo(video_id, credenciales, archivo)
            if Resultado == 1:
                Actualizados += 1
    logger.info(f"Se actualizo {Actualizados}/{total} descripciones de video")


def ActualizarThumbnails(video_id, archivo=""):
    credenciales = CargarCredenciales()
    if archivo == "":
        archivo = video_id + ".png"
    if os.path.exists(archivo):
        youtube = build("youtube", "v3", credentials=credenciales)
        Respuesta = youtube.thumbnails().set(
            videoId=video_id,
            media_body=archivo
            ).execute()
        if Respuesta['items'][0]:
            print(f"Imagen Actualizada para {video_id} - {Respuesta['items'][0]['maxres']['url']}")
        else:
            print("Hubo un problema :(")
    else:
        print(f"No existe el archivo {archivo}")
