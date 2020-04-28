
from obswebsocket import obsws, requests, events  # noqa: E402

print("Cargando OBS Web Socket")

host = "localhost"
port = 4444
password = "secret"

def CambiarHost( host_):
    global host
    host = host_;

def PreguntarHost():
    print(host);

def on_event(message):
    print(u"Got message: {}".format(message))


def on_switch(message):
    # TODO Usar info de esena para mostar en ElGato
    print(u"Cambiante de pantalla {}".format(message.getSceneName()))

def ConectarseWebSocket():
    global ConeccionOBS
    ConeccionOBS = obsws(host, port, password)
    ConeccionOBS.register(on_event)
    ConeccionOBS.register(on_switch, events.SwitchScenes)
    ConeccionOBS.connect()

def CambiarEsena(Esena):
    ConeccionOBS.call(requests.SetCurrentScene(Esena))
