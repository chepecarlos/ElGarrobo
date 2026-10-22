"""GUI de ElGarrobo con dispositivos falsos para tomar capturas: python demo_gui.py <puerto>

No lee ni escribe la config del usuario: guardar no hace nada y /modulos muestra los valores por defecto
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from nicegui import ui

from elGarrobo.accionesOOP import cargarClasesAcciones
from elGarrobo.dispositivos.dispositivo import dispositivo
from elGarrobo.dispositivos.mideck.mi_deck_combinado import MiDeckCombinado
from elGarrobo.dispositivos.migui import agregar, configuracion
from elGarrobo.dispositivos.migui import migui as moduloMiGui
from elGarrobo.dispositivos.mipedal.mi_pedal import MiPedal
from elGarrobo.dispositivos.miteclado.mi_teclado_macro import MiTecladoMacro

for nombre in ("SalvarValor", "SalvarArchivo"):
    setattr(configuracion, nombre, lambda *a, **k: None)
moduloMiGui.SalvarValor = lambda *a, **k: None
configuracion.leerData = lambda archivo: {"teclado": True, "deck_combinado": True} if archivo == "dispositivos" else {}
archivosFalsos = {
    "teclados.md": [{"nombre": "Completo", "dispositivo": "/dev/a"}],
    "deck_combinado.md": [
        {"nombre": "StreamDecks", "minutos_reposo": 10, "streamDecks": [{"nombre": "Viejo-V2", "dispositivo": "AL47I2C06277"}]}
    ],
}
configuracion.ObtenerArchivo = archivosFalsos.get

# Agregar teclado: teclados conectados falsos; en el Moonlander "se presionan" teclas
MiTecladoMacro.listarDisponibles = staticmethod(
    lambda: [("/dev/a", "DREVO BladeMaster TE 87K"), ("/dev/b", "ZSA Moonlander Mark I"), ("/dev/c", "SONiX USB DEVICE")]
)


async def escucharFalso(ruta, alPresionar):
    import asyncio

    if ruta == "/dev/b":
        for tecla in ("KEY_ESC", "KEY_A", "KEY_SPACE", "KEY_ENTER"):
            await asyncio.sleep(0.1)
            alPresionar(ruta, tecla)


agregar.escucharTeclado = escucharFalso


class dispositivoFalso(dispositivo):
    """Dispositivo sin botones físicos (como MQTT): se dibuja con la cuadrícula del folder"""

    def __init__(self, nombre: str, tipo: str, acciones: list[dict]) -> None:
        super().__init__({"nombre": nombre})
        self.tipo = tipo
        self._listaAcciones = self.convertirAcciones(acciones)

    def salvarAcciones(self):
        pass


plus = MiDeckCombinado({"nombre": "plus", "streamDecksPlus": [{"id": 0, "nombre": "Plus"}]})
plus._listaAcciones = plus.convertirAcciones(
    [
        {"nombre": "Escena", "key": 1, "accion": "escribir", "titulo": "Escena", "fondo": "#7c3aed", "opciones": {"texto": "hola"}},
        {"nombre": "Mute", "key": 2, "accion": "escribir", "titulo": "Mute", "opciones": {"texto": "m"}},
        {"nombre": "Macro", "key": 3, "accion": "macro", "opciones": [{"accion": "escribir", "opciones": {"texto": "a"}}, {"accion": "delay", "opciones": {"tiempo": 1}}]},
        {"nombre": "Volumen", "key": "dial_1", "accion": "escribir", "opciones": {"texto": "v"}},
        {"nombre": "Pantalla", "key": "touchscreen_1", "accion": "escribir", "titulo": "Hola", "opciones": {"texto": "t"}},
    ]
)
plus.accionesCargadas()
plus.listaDeck[0].baseTeclas = 1  # la asigna conectar()

pedal = MiPedal({"nombre": "pedal"})
pedal._listaAcciones = pedal.convertirAcciones(
    [
        {"nombre": "Grabar", "key": 1, "accion": "escribir", "opciones": {"texto": "hola"}},
        {"nombre": "Pausa", "key": 2, "accion": "escribir", "opciones": {"texto": "p"}},
    ]
)

teclado = MiTecladoMacro({"nombre": "teclado", "distribucion": "ingles_87k"})
teclado._listaAcciones = teclado.convertirAcciones([{"nombre": "Escena", "key": "KEY_A", "accion": "escribir", "opciones": {"texto": "a"}}])

mqtt = dispositivoFalso(
    "mqtt",
    "mqtt",
    [
        {"nombre": "Luz estudio", "key": 1, "accion": "escribir", "titulo": "Luz", "opciones": {"texto": "l"}},
        {"nombre": "Ventilador", "key": 2, "accion": "delay", "opciones": {"tiempo": 1}},
    ],
)

for aparato in (plus, pedal, teclado, mqtt):
    aparato.folderActual = "/"
    aparato.salvarAcciones = lambda: None

gui = moduloMiGui.miGui({"nombre": "gui"})
gui.listaClasesAcciones = cargarClasesAcciones()
gui.listaDispositivos = [plus, pedal, teclado, mqtt]
gui.ejecutarAcción = lambda *a, **k: None

ui.run(port=int(sys.argv[1]), reload=False, show=False, dark=True, language="es", uvicorn_logging_level="warning")
