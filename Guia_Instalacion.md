
## Clonar proyecto

TODO: Confirmar que es necesario tk
```
sudo apt intall git 
sudo apt install python3-pip python3-setuptools python3-tk python3-dev git 
git clone https://github.com/chepecarlos/ElGatoALSW.git
```


## Audio

```
sudo apt-get install -y python3-dev libasound2-dev
```

## Submodulos 

```
git submodule init
git submodule update
```

### Activar permisos de teclado

```
sudo usermod -a -G input $USER
```
Recomendacion reinicar la pc despues de agregarse a permisos

### instalar de paquetes

```
pip3 install -r requiraments.txt
pip install .
``` 





### Manejador de Ventanas

```
sudo apt install xdotool
```