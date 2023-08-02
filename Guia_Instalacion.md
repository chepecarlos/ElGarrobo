
# Guiá de instalación

## Paquetes a instalar dependencias

### Linux Mint

```bash
sudo apt install python3-pip python3-setuptools python3-tk python3-dev git 
```

### fedora 

```
 sudo dnf install python3-pip python3-setuptools python3-tkinter python3-devel git 
```

# Clonar 
Puede clonar el repositorio donde más te convenga

```
git clone https://github.com/chepecarlos/ElGatoALSW.git
```
# Entrara al folder del repositorio 
Debes entrar a la carpeta ElGatoALSW 

```
cd ElGatoALSW/
```

## Submodulos 
Ejecuta lo siguiente

```
git submodule init
git submodule update
```

## Modulos


### Control teclado USB

```
sudo usermod -a -G input $USER
```

Recomendación reiniciar la pc después de agregarse a permisos


## Audio

```
sudo apt-get install -y libasound2-dev
```

### Manejador de Ventanas

```
sudo apt install xdotool
```

### instalar de paquetes

```
pip install .
``` 

sudo apt install espeak

####### GUIA Vieja #######

### Configuraciones de StreamDeck
```bash
sudo apt install -y libhidapi-hidraw0 libudev-dev libusb-1.0-0-dev libhidapi-libusb0 zlib1g-dev
sudo usermod -a -G plugdev `whoami`
pip3 install wheel
pip3 install pillow
```

### Repoducion Sonidos
```bash
sudo apt-get install -y libasound2-dev
```

### Crear y Agregar e los archivos

sudo nano /etc/udev/rules.d/10-streamdeck.rules
```bash
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0fd9", GROUP="users"
```

sudo nano /etc/udev/rules.d/99-streamdeck.rules
```bash
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="0060", MODE:="660", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="0063", MODE:="660", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="006c", MODE:="660", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="006d", MODE:="660", GROUP="plugdev"
```

```bash
sudo udevadm control --reload-rules
pip3 install streamdeck
```


## funciones

```bash
pip3 install argparse
```
