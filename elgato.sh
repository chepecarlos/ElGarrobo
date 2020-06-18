#!/bin/bash

# TODO: Agregar mas opciones al lanzdor
# TODO: Repara eror de lanzar de otro lado k

# TODO: Crear instalador
# Agregar a ~/.bashrc
# alias elgato='bash $HOME/Programa/ElGatoALSW/elgato.sh'

# TODO: pedirle ayuda al gato para como haces un if
while [ -n "$1" ]; do
	case "$1" in
	-c)
      echo "Cargando El Gato"
      cd $HOME/5.Programas/3.App/2.Heramientas/1.ElGatoALSW
      python3 ElGatoALSW.py;;
	-s)
      echo "Cargando Servidor"
      cd $HOME/5.Programas/3.App/2.Heramientas/1.ElGatoALSW/ServerPy
      python3 Server.py;;
	*) echo "No hay opcion para $1" ;; #
  ":")
        echo "Sin valor de argumentos para la opción $OPTARG"
        ;;
	esac
	shift
done
