"""Editores de propiedades: crea el campo según el tipo, pone y lee su valor y marca errores

Los usan el formulario de acciones, los pasos de macro y la configuración de módulos
"""

import logging

import yaml
from nicegui import ui

from elGarrobo.accionesOOP import accion
from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion
from elGarrobo.miLibrerias import ConfigurarLogging

logger = ConfigurarLogging(__name__, logging.INFO)


def tipoEditor(propiedad: propiedadAccion) -> str:
    """"bool", "numero", "yaml" (dict/list) o "texto" según los tipos que acepta la propiedad"""
    tipos = set(propiedad.tipo)
    if tipos == {bool}:
        return "bool"
    if tipos and tipos <= {int, float}:
        return "numero"
    if tipos and tipos <= {dict, list}:
        return "yaml"
    return "texto"


def crearEditor(propiedad: propiedadAccion, marca: str) -> ui.element:
    """Crea el editor de una propiedad según su tipo: switch, número, YAML (dict/list) o texto; * si es obligatoria"""
    etiqueta = f"* {propiedad.nombre}" if propiedad.obligatorio else propiedad.nombre
    tipo = tipoEditor(propiedad)
    if tipo == "bool":
        editor = ui.switch(etiqueta, value=bool(propiedad.defecto))
        if propiedad.descripcion:
            editor.tooltip(propiedad.descripcion)
    else:
        if tipo == "numero":
            editor = ui.number(label=etiqueta, placeholder=propiedad.ejemplo, precision=None if float in propiedad.tipo else 0)
        elif tipo == "yaml" or propiedad.multilinea:
            editor = ui.textarea(label=etiqueta, placeholder=propiedad.ejemplo)
        else:
            editor = ui.input(label=etiqueta, placeholder=propiedad.ejemplo)
        # La ayuda queda visible debajo del campo, no en un aviso que desaparece
        ayuda = propiedad.descripcion or ""
        if tipo == "yaml":
            ayuda = f"{ayuda} (en YAML)".strip()
        if ayuda:
            editor.props["hint"] = ayuda
        editor.on_value_change(lambda _, e=editor: marcarError(e, None))
    editor.propiedad = propiedad
    editor.tipoEditor = tipo
    return editor.classes("w-full").mark(marca)


def ponerValor(editor: ui.element, valor) -> None:
    """Muestra en el editor un valor guardado en el .md según el tipo del editor"""
    tipo = getattr(editor, "tipoEditor", "texto")
    if tipo == "yaml":
        editor.value = "" if valor in (None, "") else yaml.safe_dump(valor, allow_unicode=True, sort_keys=False)
    elif tipo == "numero":
        try:
            editor.value = None if valor in (None, "") else float(valor)
        except (TypeError, ValueError):
            # Ej: guardado como texto por una versión vieja de la GUI
            editor.value = None
            marcarError(editor, f"El valor guardado no es un número: {valor}")
    elif tipo == "bool":
        editor.value = bool(valor)
    else:
        editor.value = valor


def leerValor(editor: ui.element):
    """Valor del editor con el tipo de su propiedad, None si quedó vacío; ValueError si no es válido"""
    propiedad: propiedadAccion = editor.propiedad
    valor = editor.value
    if editor.tipoEditor == "bool":
        # Solo se guarda si cambia el valor por defecto, para no llenar el .md
        return valor if propiedad.obligatorio or valor != bool(propiedad.defecto) else None
    if valor in ("", None):
        return None
    if editor.tipoEditor == "numero":
        return float(valor) if float in propiedad.tipo else int(valor)
    if editor.tipoEditor == "yaml":
        try:
            dato = yaml.safe_load(valor)
        except yaml.YAMLError as error:
            raise ValueError(f"{propiedad.nombre}: YAML con error ({getattr(error, 'problem', error)})")
        if not propiedad.mismoTipo(dato):
            tipos = " o ".join("lista" if t is list else "diccionario" for t in propiedad.tipo)
            raise ValueError(f"{propiedad.nombre}: debe ser {tipos} en YAML")
        return dato
    return valor


def nombrar(elemento: ui.element, texto: str) -> ui.element:
    """Tooltip y nombre accesible (aria-label) para botones de solo ícono"""
    elemento.props["aria-label"] = texto
    return elemento.tooltip(texto)


def encabezado(etiqueta: ui.label, nivel: int) -> ui.label:
    """Título que un lector de pantalla reconoce como encabezado (ui.label es un div)"""
    return etiqueta.props(f"role=heading aria-level={nivel}")


def marcarError(editor: ui.element, mensaje: str | None) -> None:
    """Marca (o limpia con None) el error en el campo; sin validation de nicegui hay que usar las props de Quasar"""
    if getattr(editor, "tipoEditor", None) == "bool" or isinstance(editor, ui.switch):
        return
    # None y no False al limpiar: con error=False Quasar reserva espacio para el mensaje y el campo crece.
    # No quitar la prop, nicegui lee props["error"] al cambiar el valor y daría KeyError
    editor.props["error"] = mensaje is not None or None
    editor.props["error-message"] = mensaje
    editor.update()


def avisarError(editor: ui.element, mensaje: str) -> None:
    """Marca el campo con el error y además lo avisa, por si el campo quedó fuera de la vista"""
    marcarError(editor, mensaje)
    ui.notify(mensaje, type="warning")
    logger.warning(f"Formulario[Error] {mensaje}")


def cargarOpciones(editores: dict[str, ui.element], claseAcción: type[accion], opciones: dict | list) -> None:
    """Pone en los editores las opciones guardadas en el .md"""
    objetoClase = claseAcción()
    if isinstance(opciones, list) and objetoClase.atributoLista:
        opciones = {objetoClase.atributoLista: opciones}
    if isinstance(opciones, dict):
        for propiedad in objetoClase.listaPropiedades:
            if propiedad.atributo in opciones:
                ponerValor(editores.get(propiedad.nombre), opciones[propiedad.atributo])
