import threading


def CargarHilo():
    '''Carga los todos los hilos disponibles'''
    for t in threading.enumerate():
        if t is threading.currentThread():
            continue

        if t.is_alive():
            t.join()
