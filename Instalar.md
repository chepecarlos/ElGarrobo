
# Instalacion

TODO: Competar instucciones de instalacio

Confirmar que se tiene python3
```bash
python3 --version
```

Pasos para instalacion

```bash
sudo apt update
sudo apt install python3-pip python3-setuptools python3-tk python3-dev git
git clone https://github.com/chepecarlos/ElGatoALSW.git
cd ElGatoALSW
```

### Configuraciones de StreamDeck
```bash
sudo apt install -y libhidapi-hidraw0 libudev-dev libusb-1.0-0-dev
sudo apt install -y libhidapi-libusb0
sudo apt install -y libudev-dev libusb-1.0-0-dev libhidapi-libusb0
sudo apt install -y libjpeg-dev zlib1g-dev
sudo usermod -a -G plugdev `whoami`
pip3 install wheel
pip3 install pillow
```
Agregar
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
pip3 install evdev
pip3 install argparse
pip3 install obs-websocket-py
pip3 install pyautogui
pip3 install paho-mqtt
```
