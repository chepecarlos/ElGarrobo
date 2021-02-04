
# Instalacion

TODO: Competar instucciones de Instalacion

### Instalacion de Python y Git

```bash
sudo apt update
sudo apt install python3-pip python3-setuptools python3-tk python3-dev git
git clone https://github.com/chepecarlos/ElGatoALSW.git
cd ElGatoALSW
```

### Instalar Paquetes de Python3

```bash
pip3 install -r requiraments.txt
```

```bash
pip3 freeze > paquetes.txt
```

### Configuraciones de StreamDeck
```bash
sudo apt install -y libhidapi-hidraw0 libudev-dev libusb-1.0-0-dev libhidapi-libusb0 zlib1g-dev
sudo usermod -a -G plugdev `whoami`
pip3 install wheel
pip3 install pillow
```

### Repoducion Sonidos
```bash
sudo apt-get install -y python3-dev libasound2-dev
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
# Teclados Extras

```bash
sudo usermod -a -G input $USER
```


## funciones

```bash
pip3 install argparse
```
