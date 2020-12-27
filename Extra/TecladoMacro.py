import threading

from Extra.Depuracion import Imprimir
from Extra.Acciones import Accion

from evdev import InputDevice, categorize, ecodes


class TecladoMacro:
    def __init__(self, Data):
        self.BotonesActuales = Data['teclado']
        Imprimir("Cargando Raton Razer")
        if 'Raton_Razer' in Data:
            Raton = InputDevice(Data['Raton_Razer'])
            Raton.grab()
            HiloRazer = threading.Thread(target=self.HiloRaton, args=(Raton,), daemon=True)
            HiloRazer.start()
        else:
            Imprimir("Error Teclado: Razer no definido")

    def HiloRaton(self, Raton):
        '''Hila del teclado del Raton'''
        global ComandosRaton
        for event in Raton.read_loop():
            if event.type == ecodes.EV_KEY:
                key = categorize(event)
                if key.keystate == key.key_down:
                    for teclas in ComandosRaton:
                        if 'Boton' in teclas:
                            if teclas['Boton'] == key.keycode:
                                Imprimir(f"Raton {key.keycode} - {teclas['Nombre']}")
                                Accion(teclas)
