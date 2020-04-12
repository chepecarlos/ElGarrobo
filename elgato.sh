#!/bin/bash

# TODO: Agregar mas opciones al lanzdor
# TODO: Repara eror de lanzar de otro lado k


while [ -n "$1" ]; do
	case "$1" in
	-c)
      echo "Cargando El Gato"
      cd $HOME/Programa/ElGatoALSW
      python3 ElGatoALSW.py;;
	-s)
      echo "Cargando Servidor"
      cd $HOME/Programa/ElGatoALSW/ServerPy
      python3 Server.py;;
	*) echo "No hay opcion para $1" ;; #
  ":")
        echo "Sin valor de argumentos para la opción $OPTARG"
        ;;
	esac
	shift
done
