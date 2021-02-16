from obswebsocket import obsws, requests, events

from Extra.Depuracion import Imprimir


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
        self.ConeccionOBS.register(LaFuncion)

    def Conectar(self):
        try:
            Imprimir(f"Intentando Conectar con {self.host}")
            self.ConeccionOBS = obsws(self.host, self.port)
            self.ConeccionOBS.connect()
            self.OBSConectado = True
        except Exception as e:
            Imprimir(e)
            Imprimir("No se pudo conectar a OBS")
            self.OBSConectado = False

    def CambiarGrabacion(self):
        if self.OBSConectado:
            Imprimir("Cambiando estado Grabacion")
            self.ConeccionOBS.call(requests.StartStopRecording())
        else:
            Imprimir("No se encontro OBS")

    def CambiarStriming(self):
        if self.OBSConectado:
            Imprimir("Cambiando estado Striming")
            self.ConeccionOBS.call(requests.StartStopStreaming())
        else:
            Imprimir("No se encontro OBS")

    def CambiarEsena(self, Esena):
        if self.OBSConectado:
            Imprimir("Cambiando a {}".format(Esena))
            self.ConeccionOBS.call(requests.SetCurrentScene(Esena))
        else:
            Imprimir("No se encontro OBS")

    def CambiarVolumen(self, Fuente):
        if self.OBSConectado:
            Imprimir("Cambiando estado Volumen {}".format(Fuente))
            self.ConeccionOBS.call(requests.ToggleMute(Fuente))
        else:
            Imprimir("No se encontro OBS")

    def CambiarFiltro(self, Fuente, Filtro, Estado):
        '''Funcion que cambia el estado de un filtro'''
        if self.OBSConectado:
            Imprimir(f"Cambiando del Filtro {Filtro} de {Fuente} a {not Estado}")
            self.ConeccionOBS.call(requests.SetSourceFilterVisibility(Fuente, Filtro, not Estado))
        else:
            Imprimir("No se encontro OBS")

    def CambiarFuente(self, Fuente, Estado):
        if self.OBSConectado:
            Imprimir(f"Cambiando Fuente {Fuente} - {Estado}")
            self.ConeccionOBS.call(requests.SetSceneItemProperties(Fuente, visible=Estado))
        else:
            Imprimir("No se encontro OBS")

    def Cerrar(self):
        if self.OBSConectado:
            Imprimir("Cerrando OBS")
            self.ConeccionOBS.disconnect()
