import os
import pickle
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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


def ActualizarDescripcion(video_id, arhivo=""):
    credenciales = CargarCredenciales()
    if arhivo:
        print(f"Archivo existe y es {arhivo}")
    else:
        print("No existe archivo")

    youtube = build("youtube", "v3", credentials=credenciales)

    SolisitudVideo = youtube.videos().list(
        id=video_id,
        part='snippet'
      )

    DataVideo = SolisitudVideo.execute()
    SnippetVideo = DataVideo["items"][0]["snippet"]

    SnippetVideo["description"] = "pollo 2 el regreso el pollo"

    SolisituActualizar = youtube.videos().update(
        part='snippet',
        body=dict(
          snippet=SnippetVideo,
          id=video_id
        ))

    RespuestaYoutube = SolisituActualizar.execute()
    print(RespuestaYoutube)
