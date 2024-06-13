
# Guiá de instalación

## Paquetes a instalar dependencias

### Linux Mint

```bash
sudo apt install python3-pip python3-setuptools python3-tk python3-dev ffmpeg git 
```

### fedora 

```bash
sudo dnf install python3-pip python3-setuptools python3-tkinter python3-devel git 
```

# Clonar 
Puede clonar el repositorio donde más te convenga

```bash
git clone https://github.com/chepecarlos/ElGarrobo
```
# Entrara al folder del repositorio 
Debes entrar a la carpeta ElGatoALSW 

```bash
cd ElGarrobo
```

## Submodulos 
Ejecuta lo siguiente

```bash
git submodule init
git submodule update
```

## Modulos


### Control teclado USB

```bash
sudo usermod -a -G input $USER
```

Recomendación reiniciar la pc después de agregarse a permisos

## Audio

```bash
sudo apt-get install -y libasound2-dev
```

### Manejador de Ventanas

```bash
sudo apt install xdotool
```

### Sintetizador de voz

```bash
sudo apt install espeak
```

### instalar de paquetes

```bash
pip install .
``` 

## Agregar binarios a sistema 

```bash
echo 'PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```








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
