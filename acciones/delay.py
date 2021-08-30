"""Modulo de Tiempo."""
import time


def Delay(opciones):
    """
    Hace una pequeña espera en segundos.
    
    tiempo -> float 
        tiempo de espera en segundos
    """
    if 'tiempo' in opciones:
        time.sleep(opciones['tiempo'])
