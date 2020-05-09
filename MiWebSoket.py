import websocket
#
# def ComandoWebSocket(comando):
#     if 'Servidor' in data:
#         ws = websocket.WebSocket()
#
#         print(Servidor)
#         ws.connect(Servidor)
#         ws.send(comando)
#         # print ("Reciviendo...")
#         # result = ws.recv()
#         print (f"comando enviado")
#         ws.close()

class MiWebSoket:
    def __init__(self):
        self.host = "localhost"
        self.port = 4444
        self.WebSocketConectado = False

    def CambiarHost(self, host_):
        self.host = host_;

    def Conectar(self):
        try:
            self.ws = websocket.WebSocket()
            self.Servidor = "ws://{}:8765".format(self.host)
            self.ws.connect(self.Servidor)
            self.WebSocketConectado = True
            # self.result =  self.ws.recv()
            # print("Received '%s'" % self.result)
            print("Conectado")
        except:
            print("No se pudo conectar a WebSocket")
            self.WebSocketConectado = False

    def Enviar(self, EnviarValor):
        if self.WebSocketConectado:
            print("Enviando datos")
            self.ws.send(EnviarValor)
        else:
            print("No conectado a WebSocket")

    def Cerrar(self):
        if self.WebSocketConectado:
            print("Cerrando WebSocket")
            ws.close()
