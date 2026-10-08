"""Convierte el JSON de keyboard-layout-editor.com (KLE) a la distribución de ElGarrobo.

En KLE cada fila es una lista; un dict cambia la posición/tamaño de la siguiente tecla y un texto es una tecla
con sus leyendas separadas por "\\n". El keycode se saca de la leyenda: "KEY_F13" se usa tal cual, si no se
busca "KEY_" + leyenda ("Q", "F1", "Tab") o un alias ("Shift", "←", "PgUp").
"""

import html
import re

from evdev import ecodes

# ponytail: la rotación de KLE (r, rx, ry) se ignora, solo se usan x, y, w, h; agregar si alguien dibuja teclados ergonómicos
alias = {
    "`": "GRAVE", "-": "MINUS", "=": "EQUAL", "[": "LEFTBRACE", "]": "RIGHTBRACE", "\\": "BACKSLASH",
    ";": "SEMICOLON", "'": "APOSTROPHE", ",": "COMMA", ".": "DOT", "/": "SLASH",
    "BACKSPACE": "BACKSPACE", "⌫": "BACKSPACE", "CAPS LOCK": "CAPSLOCK", "CAPS": "CAPSLOCK", "RETURN": "ENTER",
    "SHIFT": ["LEFTSHIFT", "RIGHTSHIFT"], "CTRL": ["LEFTCTRL", "RIGHTCTRL"], "ALT": ["LEFTALT", "RIGHTALT"],
    "ALTGR": "RIGHTALT", "WIN": ["LEFTMETA", "RIGHTMETA"], "SUPER": ["LEFTMETA", "RIGHTMETA"], "MENU": "COMPOSE",
    "←": "LEFT", "↑": "UP", "→": "RIGHT", "↓": "DOWN",
    "PGUP": "PAGEUP", "PAGE UP": "PAGEUP", "PGDN": "PAGEDOWN", "PAGE DOWN": "PAGEDOWN",
    "INS": "INSERT", "DEL": "DELETE", "PRTSC": "SYSRQ", "PRINT SCREEN": "SYSRQ", "SCROLL LOCK": "SCROLLLOCK",
    "SCRLK": "SCROLLLOCK", "PAUSE BREAK": "PAUSE", "NUM LOCK": "NUMLOCK", "": "SPACE",
}


def limpiarLeyenda(texto: str) -> str:
    return html.unescape(re.sub(r"<[^>]*>", "", texto)).strip()


def buscarKeycode(leyendas: list[str], usadas: set[str]) -> tuple[str, str] | tuple[None, None]:
    """Primer keycode válido y libre que sale de las leyendas, con la leyenda que lo dio"""
    for leyenda in leyendas:
        if leyenda.startswith("KEY_"):
            opciones = [leyenda]
        else:
            nombre = alias.get(leyenda.upper(), leyenda.upper().replace(" ", ""))
            opciones = ["KEY_" + n for n in (nombre if isinstance(nombre, list) else [nombre])]
        for keycode in opciones:
            if keycode in ecodes.ecodes and keycode not in usadas:
                return keycode, leyenda
    return None, None


def convertirKLE(data: list) -> list[dict]:
    """Distribución de ElGarrobo a partir del JSON "raw" de KLE; las teclas sin keycode se omiten"""
    teclas = []
    usadas = set()
    y = 0.0
    for fila in data:
        if not isinstance(fila, list):
            continue  # metadatos del teclado (nombre, autor)
        x, w, h = 0.0, 1.0, 1.0
        for elemento in fila:
            if isinstance(elemento, dict):
                x += elemento.get("x", 0)
                y += elemento.get("y", 0)
                w, h = elemento.get("w", w), elemento.get("h", h)
                continue
            leyendas = [limpiarLeyenda(parte) for parte in str(elemento).split("\n")]
            leyendas = [parte for parte in leyendas if parte] or [""]
            keycode, leyenda = buscarKeycode(leyendas, usadas)
            if keycode is not None:
                usadas.add(keycode)
                tecla = {"key": keycode, "x": x, "y": y}
                if w != 1:
                    tecla["w"] = w
                if h != 1:
                    tecla["h"] = h
                # Con KEY_ en la leyenda la etiqueta es la otra leyenda (ej. "KEY_F13\nG1" → G1)
                etiqueta = next((parte for parte in leyendas if not parte.startswith("KEY_")), "") if leyenda.startswith("KEY_") else leyenda
                if etiqueta and "KEY_" + etiqueta.upper() != keycode:
                    tecla["etiqueta"] = etiqueta
                teclas.append(tecla)
            x += w
            w, h = 1.0, 1.0
        y += 1
    return teclas
