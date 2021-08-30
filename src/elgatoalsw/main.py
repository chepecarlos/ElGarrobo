import argparse
import os
import sys

def Parametros():

    parser = argparse.ArgumentParser(
        description='Heramientas de Macros de ALSW')
    parser.add_argument('--nodepurar', '-nd', help="Acivar modo sin depuracion", action="store_true")
    parser.add_argument( '--gui', '-g', help="Sistema interface grafica", action="store_true")

    return parser.parse_args()


def main():
    print("Iniciando EL Nuevo ElGatoALSW")
    args = Parametros()


if __name__ == "__main__":
    main()
    exit()