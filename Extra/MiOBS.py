from obswebsocket import obsws, requests, events


def EventoOBS(mensaje):
    '''Escucha y Reaciona a eventos de OBS'''
    print(f"Evento OBS {mensaje.name}")
    if mensaje.name == "Exiting":
        print("Cerrando OBS")


class MiObsWS:
    def __init__(self):
        self.host = "localhost"
        self.port = 4444
        self.OBSConectado = False

    def CambiarHost(self, host_):
        self.host = host_

    def RegistarCambioEsena(self, LaFuncion):
        self.ConeccionOBS.register(LaFuncion, events.SwitchScenes)

    def RegistarEvento(self, LaFuncion):
        if self.OBSConectado:
            self.ConeccionOBS.register(LaFuncion)
        else:
            print("No se encontro OBS")

    def DesregistarEvento(self, LaFuncion):
        if self.OBSConectado:
            self.ConeccionOBS.unregister(LaFuncion)
        else:
            print("No se encontro OBS")

    def Conectar(self):
        try:
            print(f"Intentando Conectar con {self.host}")
            self.ConeccionOBS = obsws(self.host, self.port)
            self.ConeccionOBS.connect()
            self.OBSConectado = True
        except Exception as e:
            print(e)
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

    def CambiarVolumen(self, Fuente):
        if self.OBSConectado:
            print("Cambiando estado Volumen {}".format(Fuente))
            self.ConeccionOBS.call(requests.ToggleMute(Fuente))
        else:
            print("No se encontro OBS")

    def CambiarFiltro(self, Fuente, Filtro, Estado):
        '''Funcion que cambia el estado de un filtro'''
        if self.OBSConectado:
            print(f"Cambiando del Filtro {Filtro} de {Fuente} a {not Estado}")
            self.ConeccionOBS.call(requests.SetSourceFilterVisibility(Fuente, Filtro, not Estado))
        else:
            print("No se encontro OBS")

    def CambiarFuente(self, Fuente, Estado):
        if self.OBSConectado:
            print(f"Cambiando Fuente {Fuente} - {Estado}")
            self.ConeccionOBS.call(requests.SetSceneItemProperties(Fuente, visible=Estado))
        else:
            print("No se encontro OBS")

    def Cerrar(self):
        if self.OBSConectado:
            print("Cerrando OBS")
            self.ConeccionOBS.disconnect()
