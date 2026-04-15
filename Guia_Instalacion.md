
# Guía de instalación

## Paquetes a instalar dependencias

### Linux Mint

Preparar paquete básicos para preparar la instalación

```bash
sudo apt update && sudo apt dist-upgrade -y
sudo apt install -y git python3-pip python3-setuptools python3-tk python3-dev pipx ffmpeg git xdotool
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
Descarga sub modulos 

```bash
git submodule init
git submodule update
```

## Modulos


### Control teclado USB

Para controlar tecaldos 

```bash
sudo usermod -a -G input $USER
```

Recomendación reiniciar la pc después de agregarse a permisos

### Audio

Paquetes extras para poder reproducir sonidos 

```bash
sudo apt install -y libportaudio2 libsndfile1 libasound2-dev
```

### Configurar StreamDeck

Para configurar para diferentes versiones
```bash
sudo apt install -y libudev-dev libusb-1.0-0-dev libhidapi-libusb0
sudo apt install -y libjpeg-dev zlib1g-dev libopenjp2-7 libtiff6
``` 

crear el archivo /etc/udev/rules.d/10-streamdeck.rules y escribiri
```bash
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0fd9", GROUP="users", TAG+="uaccess"
```

reiniciar colección por usb con StreamDeck

```bash
sudo udevadm control --reload-rules
```
desconectar y conectar el Stramdeck

### Manejador de Ventanas

```bash
sudo apt install xdotool
```

### Sintetizador de voz

```bash
sudo apt install espeak
```

## Configurar pipx
Agregar gestor de paquetes de python pipx, para instalar paquetes en el sistema

```bash
pipx ensurepath
pipx completions
```

### instalar de paquetes

```bash
pipx install .
``` 

## Reiniciar PC 

Para aplicar los permisos de usb se necesita reiniciar la computadora






####### GUIA Vieja #######

### Configuraciones de StreamDeck
```bash
sudo apt install -y libhidapi-hidraw0 libudev-dev libusb-1.0-0-dev libhidapi-libusb0 zlib1g-dev
sudo apt install -y libjpeg-dev zlib1g-dev libopenjp2-7 libtiff6

sudo usermod -a -G plugdev `whoami`
pip3 install wheel
pip3 install pillow
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

recargar modulos de 
```bash
sudo udevadm control --reload-rules
```
