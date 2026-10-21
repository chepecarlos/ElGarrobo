"""Capturas de la GUI en tema oscuro y claro para revisarlas a ojo: make capturas

Levanta demo_gui.py en un puerto libre, recorre las pantallas con Playwright usando el Google Chrome del sistema
y guarda los PNG en capturas/ (se borra en cada corrida)
"""

import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

RAIZ = Path(__file__).parents[2]
CARPETA = RAIZ / "capturas"


def puertoLibre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def esperarServidor(url: str, servidor: subprocess.Popen, segundos: int = 30) -> None:
    for _ in range(segundos * 4):
        if servidor.poll() is not None:
            raise RuntimeError("demo_gui.py terminó antes de arrancar")
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except OSError:
            time.sleep(0.25)
    raise TimeoutError(f"La GUI de demo no respondió en {url}")


def esperar(página: Page, segundos: float = 0.6) -> None:
    página.wait_for_load_state("networkidle")
    time.sleep(segundos)  # animaciones de Quasar (diálogos, navegación)


def foto(página: Page, nombre: str) -> None:
    página.screenshot(path=str(CARPETA / f"{nombre}.png"))
    print(f"  {nombre}.png")


def botón(página: Page, nombre: str):
    return página.get_by_role("button", name=nombre, exact=True)


def pestaña(página: Page, nombre: str) -> None:
    página.locator(".q-tab").get_by_text(nombre, exact=True).click()
    esperar(página)


def recorrer(navegador, url: str, tema: str) -> None:
    t = tema.lower()
    página = navegador.new_page(viewport={"width": 1440, "height": 900})

    página.goto(f"{url}/configurar")
    esperar(página)
    página.locator(".q-btn-toggle").get_by_text(tema, exact=True).click()
    esperar(página)
    foto(página, f"{t}-configurar")

    página.goto(f"{url}/")
    esperar(página, 1)
    foto(página, f"{t}-acciones")

    botón(página, "Agregar acción").click()
    esperar(página)
    foto(página, f"{t}-formulario-errores")

    botón(página, "Escena").first.click()
    esperar(página)
    foto(página, f"{t}-formulario-editar")
    botón(página, "Editar apariencia").click()
    esperar(página)
    foto(página, f"{t}-dialogo-apariencia")
    página.keyboard.press("Escape")
    esperar(página)

    botón(página, "Macro").first.click()
    esperar(página)
    botón(página, "Editar pasos").click()
    esperar(página)
    foto(página, f"{t}-dialogo-pasos")
    página.keyboard.press("Escape")
    esperar(página)

    pestaña(página, "teclado")
    foto(página, f"{t}-teclado")

    pestaña(página, "mqtt")
    foto(página, f"{t}-mqtt")

    pestaña(página, "pedal")
    botón(página, "Vista lista").click()
    esperar(página)
    foto(página, f"{t}-lista")
    botón(página, "Apariencia del folder").click()
    esperar(página)
    foto(página, f"{t}-dialogo-folder")
    página.keyboard.press("Escape")
    esperar(página)

    for _ in range(3):
        página.keyboard.press("Tab")
    esperar(página, 0.3)
    foto(página, f"{t}-foco")

    página.locator(".modo-toggle").get_by_text("Usar", exact=True).click()
    esperar(página, 1)
    pestaña(página, "plus")
    foto(página, f"{t}-usar")
    página.locator(".modo-toggle").get_by_text("Editar", exact=True).click()
    esperar(página)

    página.goto(f"{url}/modulos")
    esperar(página)
    página.locator(".q-expansion-item").first.click()
    esperar(página)
    foto(página, f"{t}-modulos")
    página.close()

    celular = navegador.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    celular.goto(f"{url}/")
    esperar(celular, 1)
    foto(celular, f"{t}-celular")
    celular.close()


def main() -> None:
    shutil.rmtree(CARPETA, ignore_errors=True)
    CARPETA.mkdir()
    puerto = puertoLibre()
    url = f"http://127.0.0.1:{puerto}"
    registro = open(CARPETA / "demo_gui.log", "w")
    servidor = subprocess.Popen([sys.executable, str(Path(__file__).with_name("demo_gui.py")), str(puerto)], stdout=registro, stderr=subprocess.STDOUT)
    try:
        esperarServidor(url, servidor)
        with sync_playwright() as p:
            navegador = p.chromium.launch(channel="chrome")
            for tema in ("Oscuro", "Claro"):
                print(f"Tema {tema.lower()}:")
                recorrer(navegador, url, tema)
            navegador.close()
    finally:
        servidor.terminate()
        servidor.wait(timeout=10)
        registro.close()


if __name__ == "__main__":
    main()
