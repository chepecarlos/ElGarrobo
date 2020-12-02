from obswebsocket import obsws, requests, events


class MiObsWS:
    def __init__(self, _Carpeta):
        self.host = "localhost"
        self.port = 4444
        self.OBSConectado = False
        self.Carpeta = _Carpeta

    def CambiarHost(self, host_):
        self.host = host_

    def RegistarCambioEsena(self, LaFuncion):
        self.ConeccionOBS.register(LaFuncion, events.SwitchScenes)

    def RegistarEvento(self, LaFuncion):
        if self.OBSConectado:
            self.ConeccionOBS.register(LaFuncion)
        else:
            print("OBS no Conectado")

    def DesregistarEvento(self, LaFuncion):
        if self.OBSConectado:
            self.ConeccionOBS.unregister(LaFuncion)
        else:
            print("OBS no Conectado")

    def Conectar(self):
        try:
            print(f"Intentando Conectar con {self.host} - {self.Carpeta}")
            self.ConeccionOBS = obsws(self.host, self.port)
            self.ConeccionOBS.connect()
            self.OBSConectado = True
        except Exception as e:
            print(f"No se pudo conectar a OBS {e}")
            self.OBSConectado = False

    def CambiarGrabacion(self):
        if self.OBSConectado:
            print("Cambiando estado Grabacion")
            self.ConeccionOBS.call(requests.StartStopRecording())
        else:
            print("OBS no Conectado")

    def CambiarStriming(self):
        if self.OBSConectado:
            print("Cambiando estado Striming")
            self.ConeccionOBS.call(requests.StartStopStreaming())
        else:
            print("OBS no Conectado")

    def CambiarEsena(self, Esena):
        if self.OBSConectado:
            print("Cambiando a {}".format(Esena))
            self.ConeccionOBS.call(requests.SetCurrentScene(Esena))
        else:
            print("OBS no Conectado")

    def CambiarVolumen(self, Fuente):
        if self.OBSConectado:
            print("Cambiando estado Volumen {}".format(Fuente))
            self.ConeccionOBS.call(requests.ToggleMute(Fuente))
        else:
            print("OBS no Conectado")

    def CambiarFiltro(self, Fuente, Filtro, Estado):
        '''Funcion que cambia el estado de un filtro'''
        if self.OBSConectado:
            print(f"Cambiando del Filtro {Filtro} de {Fuente} a {Estado}")
            self.ConeccionOBS.call(requests.SetSourceFilterVisibility(Fuente, Filtro, Estado))
        else:
            print("OBS no Conectado")

    def CambiarFuente(self, Fuente, Estado):
        if self.OBSConectado:
            print(f"Cambiando Fuente {Fuente} - {Estado}")
            self.ConeccionOBS.call(requests.SetSceneItemProperties(Fuente, visible=Estado))
        else:
            print("OBS no Conectado")

    def Cerrar(self):
        if self.OBSConectado:
            print("Cerrando OBS")
            self.ConeccionOBS.disconnect()
