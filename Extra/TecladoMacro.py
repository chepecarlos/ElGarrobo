import threading

from Extra.Depuracion import Imprimir
from Extra.Acciones import Accion
from Extra.CargarData import ExisteArchivo, CargarValores
from evdev import InputDevice, categorize, ecodes


class TecladoMacro:
    def __init__(self, Nombre_, Dispisitivo_, File_):
        self.Nombre = Nombre_
        self.Dispisitivo = Dispisitivo_
        self.File = File_

    def Conectar(self):
        try:
            self.Teclado = InputDevice(self.Dispisitivo)
            self.Teclado.grab()
            self.HiloTeclado = threading.Thread(target=self.HiloRaton, args=(self.Teclado,self.Nombre,), daemon=True)
            self.HiloTeclado.start()
            Imprimir(f"Conectando a Teclado {self.Nombre}")
        except:
            Imprimir(f"No se encontro el Teclado {self.Nombre}")
            return False
        return True

    def ActualizarTeclas(self, Archivo):
        if ExisteArchivo(Archivo + "/" + self.File, True):
            print(f"Cargando Archivo {self.File}")
            self.TeclasActuales = CargarValores(Archivo + "/" + self.File, True)
        else:
            print(f"No se encontro el {Archivo}")

    def HiloRaton(self, Teclado, Nombre):
        '''Hila del teclado del Teclado'''
        for event in Teclado.read_loop():
            if event.type == ecodes.EV_KEY:
                key = categorize(event)
                if key.keystate == key.key_down:
                    Encontrado = False
                    for Boton in self.TeclasActuales:
                        if 'KEY' in Boton:
                            if Boton['KEY'] == key.keycode:
                                Imprimir(f"Teclado {Nombre} - {key.keycode}")
                                Accion(Boton)
                                Encontrado = True
                    if not Encontrado:
                        Imprimir(f"Teclado {Nombre} - No programado {key.keycode}")
