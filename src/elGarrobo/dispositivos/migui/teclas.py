"""Utilidades de las teclas de un dispositivo: buscar repetidas, ordenar y medir"""

unidadTecla = 112
"Pixeles de una tecla de 1x1 en la distribución del teclado: resolución del dibujo y tamaño máximo en pantalla"


def teclaRepetida(listaAcciones: list[dict], tecla, ignorar: dict = None) -> dict:
    """Devuelve la acción que ya usa la tecla (sin contar ignorar), o None"""
    for acción in listaAcciones:
        if acción is not ignorar and str(acción.get("key")) == str(tecla):
            return acción
    return None


def ordenTecla(acción: dict) -> tuple:
    """Números primero (streamdeck/pedal), luego texto (teclados), sin comparar int con str"""
    tecla = acción.get("key")
    return (0, tecla, "") if isinstance(tecla, int) else (1, 0, str(tecla))


def ordenarAcciones(listaAcciones: list[dict], campo: str, inverso: bool = False) -> list[dict]:
    """Copia ordenada de las acciones por "nombre", "titulo", "key" o "accion", sin tocar la lista guardada"""
    if campo == "key":
        orden = ordenTecla
    else:
        orden = lambda acción: str(acción.get(campo) or "").lower()
    return sorted(listaAcciones, key=orden, reverse=inverso)


def tamañoTecla(teclaFisica: dict) -> tuple[int, int]:
    """Ancho y alto en pixeles de una tecla de la distribución, dejando 4px de separación"""
    return (int(teclaFisica.get("w", 1) * unidadTecla) - 4, int(teclaFisica.get("h", 1) * unidadTecla) - 4)
