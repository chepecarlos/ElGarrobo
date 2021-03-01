import threading
import logging

from Extra.FuncionesLogging import ConfigurarLogging
from Extra.Depuracion import Imprimir
from Extra.Acciones import Accion
from Extra.CargarData import ExisteArchivo, CargarValores
from evdev import InputDevice, categorize, ecodes

logger = logging.getLogger(__name__)
ConfigurarLogging(logger)

class MiTecladoMacro:
    def __init__(self, Nombre, Dispisitivo, File):
        self.Nombre = Nombre
        self.Dispisitivo = Dispisitivo
        self.File = File

    def Conectar(self):
        try:
            self.Teclado = InputDevice(self.Dispisitivo)
            self.Teclado.grab()
            self.HiloTeclado = threading.Thread(target=self.HiloRaton, args=(self.Teclado, self.Nombre,), daemon=True)
            self.HiloTeclado.start()
            logger.info(f"Conectando: {self.Nombre} - {self.Dispisitivo}")
        except:
            logger.warning(f"Conectando a Teclado {self.Nombre}")
            return False
        return True

    def ActualizarTeclas(self, Archivo):
        if ExisteArchivo(Archivo + "/" + self.File, True):
            Imprimir(f"Cargando Archivo {self.File}")
            self.TeclasActuales = CargarValores(Archivo + "/" + self.File, True)

    def HiloRaton(self, Teclado, Nombre):
        '''Hila del teclado del Teclado'''
        for event in Teclado.read_loop():
            if event.type == ecodes.EV_KEY:
                key = categorize(event)
                if key.keystate == key.key_down:
                    logger.debug(f"Evento {Nombre} - {key.keycode}")
                    # Imprimir(f"Teclado {Nombre} - {key.keycode}")
                    # Encontrado = False
                    # for Boton in self.TeclasActuales:
                    #     if 'KEY' in Boton:
                    #         if Boton['KEY'] == key.keycode:
                    #             Imprimir(f"Teclado {Nombre} - {key.keycode}")
                    #             Accion(Boton)
                    #             Encontrado = True
                    # if not Encontrado:
                    #     Imprimir(f"Teclado {Nombre} - No programado {key.keycode}")
