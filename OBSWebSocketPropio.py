from obswebsocket import obsws, requests, events

def on_event(message):
    print()
    if(message.name == 'RecordingStopped'):
        print('Se paro la grabacion')
    elif(message.name == 'RecordingStarted'):
        print('Se Inicio la grabacion')
    elif(message.name == 'SourceMuteStateChanged'):
        print(f"[Evento] - Sonido de {message.datain['sourceName']} - {message.datain['muted']}")
    elif(message.name == 'SourceFilterVisibilityChanged'):
        print(f"[Evento] Filtro {message.datain['filterName']} de {message.datain['sourceName']} - {message.datain['filterEnabled']}")
    else:
        print(f"Mensaje OBS-WebSocket: {message}")


def on_switch(message):
    #TODO Usar info de esena para mostar en ElGato
    print(f"Cambiante de pantalla {message.getSceneName()}")

class MiObsWS:
    def __init__(self):
        self.host = "localhost"
        self.port = 4444
        self.OBSConectado = False

    def CambiarHost(self, host_):
        self.host = host_;

    def Conectar(self):
        try:
            print(f"Intentando Conectar con {self.host}")
            self.ConeccionOBS = obsws(self.host, self.port)
            self.ConeccionOBS.register(on_event)
            self.ConeccionOBS.register(on_switch, events.SwitchScenes)
            self.ConeccionOBS.connect()
            self.OBSConectado = True
        except :
            print("No se pudo conectar a OBS")
            self.OBSConectado = False

    def CambiarGrabacion(self):
        if self.OBSConectado:
            print("Cambiando estado Grabacion")
            self.ConeccionOBS.call(requests.StartStopRecording())
        else:
            print("No se encontro OBS")

    def CambiarStriming(self):
        if self.OBSConectado:
            print("Cambiando estado Striming")
            self.ConeccionOBS.call(requests.StartStopStreaming())
        else:
            print("No se encontro OBS")

    def CambiarEsena(self, Esena):
        if self.OBSConectado:
            print("Cambiando a {}".format(Esena))
            self.ConeccionOBS.call(requests.SetCurrentScene(Esena))
        else:
            print("No se encontro OBS")

    # def Prueva(self, dato):
    #     dato['Comando'][4]['Key'][0]['Estado'] = True

    def CambiarVolumen(self, Fuente):
        if self.OBSConectado:
            print("Cambiando estado Volumen {}".format(Fuente))
            self.ConeccionOBS.call(requests.ToggleMute(Fuente))
        else:
            print("No se encontro OBS")

    def CambiarFiltro(self, Fuente, Filtro, Estado):
        if self.OBSConectado:
            print("Cambiando del Filtro {} de {} a {}".format(Filtro, Fuente, Estado))
            self.ConeccionOBS.call(requests.SetSourceFilterVisibility(Fuente, Filtro, Estado))
        else:
            print("No se encontro OBS")

    def CambiarFuente(self, Fuente, Estado):
        print("Cambiando Fuente {Fuente} - {Estado}")
        # pollo = Baserequests()
        # pollo.datain['item-visible'] = Estado
        # pollo = {'item-visible': Estado}
        # print(pollo)
        # GetSourceSettings
        # pollo = self.ConeccionOBS.call(requests.GetSourceSettings(Fuente))
        # print("polo es {}".format(pollo)).getSourcesettings()
        self.ConeccionOBS.call(requests.SetSourceSettings(Fuente, {'item-id': 7, 'item-name': 'Camara', 'item-visible': False, 'scene-name': 'Ozmaro'}))
