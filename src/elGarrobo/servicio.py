"""
Servicio de systemd de usuario, ícono de la barra de estado (bandeja.py) y entrada en el menú.
Lo usan `elgarrobo servicio instalar/desinstalar` y la página /configurar de la GUI.
"""

import os
import subprocess
import sys
from pathlib import Path


def autoarranque() -> Path:
    """Archivo que hace que la bandeja (y con ella ElGarrobo) arranque al iniciar sesión"""
    return Path.home() / ".config/autostart/elgarrobo.desktop"


def archivosServicio() -> dict[Path, str]:
    """Archivos que se instalan, con la ruta real del ejecutable (pipx o venv)"""
    ejecutable = os.path.abspath(sys.argv[0])
    bandeja = Path(__file__).with_name("bandeja.py")
    escritorio = f"""[Desktop Entry]
Type=Application
Name=ElGarrobo
Comment=Macros para StreamDeck, teclados, MQTT y OBS
Exec=/usr/bin/python3 {bandeja} {ejecutable}
Icon=input-keyboard
Terminal=false
Categories=Utility;
X-GNOME-Autostart-Delay=5
"""
    # Sin [Install]: no arranca solo, lo arranca la bandeja ya con la sesión gráfica lista
    servicio = f"""[Unit]
Description=ElGarrobo - Macros para StreamDeck, teclados, MQTT y OBS
# 3 fallos en 60s → queda en 'failed' y la bandeja avisa; con los valores por defecto y RestartSec=3 nunca se rinde
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
ExecStart={ejecutable}
Restart=on-failure
RestartSec=3
"""
    home = Path.home()
    return {
        home / ".config/systemd/user/elgarrobo.service": servicio,
        home / ".local/share/applications/elgarrobo.desktop": escritorio,
        autoarranque(): escritorio,
    }


def instalar() -> list[Path]:
    """Crea los archivos del servicio; devuelve los creados"""
    archivos = archivosServicio()
    for archivo, contenido in archivos.items():
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(contenido)
    subprocess.run(["systemctl", "--user", "daemon-reload"])
    return list(archivos)


def desinstalar() -> list[Path]:
    """Detiene el servicio y borra sus archivos; devuelve los borrados"""
    subprocess.run(["systemctl", "--user", "stop", "elgarrobo"])
    archivos = list(archivosServicio())
    for archivo in archivos:
        archivo.unlink(missing_ok=True)
    subprocess.run(["systemctl", "--user", "daemon-reload"])
    return archivos


def cambiarAutoarranque(activar: bool) -> None:
    """Activar reinstala todo (por si falta el servicio); desactivar solo quita el archivo de autostart"""
    if activar:
        instalar()
    else:
        autoarranque().unlink(missing_ok=True)
