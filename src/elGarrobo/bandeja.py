"""
Ícono en la barra de estado para controlar el servicio de ElGarrobo (systemd de usuario).

Corre con el Python del sistema (/usr/bin/python3) porque necesita `gi`, que no está en el venv/pipx;
por eso solo usa la librería estándar y no importa nada de elGarrobo.
Uso: /usr/bin/python3 bandeja.py <ruta del ejecutable elgarrobo>
"""

import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3 as AppIndicator
from gi.repository import GLib, Gtk

SERVICIO = "elgarrobo"
# ponytail: íconos genéricos del tema mientras se crea el logo propio
ESTADOS = {
    "activo": ("media-playback-start", "ElGarrobo activo"),
    "iniciando": ("view-refresh", "ElGarrobo iniciando..."),
    "detenido": ("media-playback-stop", "ElGarrobo detenido"),
    "error": ("dialog-error", "ElGarrobo con error (revisa los logs)"),
}
# Variables de la sesión gráfica que el servicio necesita (teclado simulado, notificaciones, navegador)
VARIABLES_SESION = ["DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "XDG_CURRENT_DESKTOP"]


def systemctl(*argumentos: str) -> str:
    resultado = subprocess.run(["systemctl", "--user", *argumentos], capture_output=True, text=True)
    return resultado.stdout.strip()


def estadoServicio() -> str:
    """Traduce el estado de systemd: con Restart=on-failure un crash pasa por 'activating' y termina en 'failed'"""
    estado = systemctl("is-active", SERVICIO)
    if estado == "active":
        return "activo"
    if estado in ("activating", "reloading"):
        return "iniciando"
    if estado == "failed":
        return "error"
    return "detenido"


class bandeja(Gtk.Application):
    def __init__(self, ejecutable: str) -> None:
        # application_id hace que una segunda instancia se cierre sola (DBus)
        super().__init__(application_id="com.chepecarlos.elgarrobo.bandeja")
        self.ejecutable = ejecutable
        self.indicador = None
        self.estado = None

    def do_activate(self) -> None:
        if self.indicador:
            return
        self.hold()
        self.indicador = AppIndicator.Indicator.new(
            "elgarrobo", ESTADOS["detenido"][0], AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicador.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.crearMenu()

        if estadoServicio() != "activo":
            self.iniciar()
        self.actualizar()
        GLib.timeout_add_seconds(2, self.actualizar)

    def crearMenu(self) -> None:
        menu = Gtk.Menu()
        self.etiquetaEstado = Gtk.MenuItem(label="")
        self.etiquetaEstado.set_sensitive(False)
        menu.append(self.etiquetaEstado)
        menu.append(Gtk.SeparatorMenuItem())

        def opcion(texto, funcion):
            item = Gtk.MenuItem(label=texto)
            item.connect("activate", lambda _: funcion())
            menu.append(item)
            return item

        self.opcionGUI = opcion("Abrir GUI", self.abrirGUI)
        self.opcionIniciar = opcion("Iniciar", self.iniciar)
        self.opcionReiniciar = opcion("Reiniciar", self.reiniciar)
        self.opcionDetener = opcion("Detener", self.detener)
        opcion("Ver logs", self.verLogs)
        menu.append(Gtk.SeparatorMenuItem())
        opcion("Salir", self.salir)

        menu.show_all()
        self.indicador.set_menu(menu)

    def actualizar(self) -> bool:
        estado = estadoServicio()
        if estado != self.estado:
            self.estado = estado
            icono, texto = ESTADOS[estado]
            self.indicador.set_icon_full(icono, texto)
            self.indicador.set_title(texto)
            self.etiquetaEstado.set_label(texto)
            activo = estado in ("activo", "iniciando")
            self.opcionGUI.set_sensitive(estado == "activo")
            self.opcionIniciar.set_sensitive(not activo)
            self.opcionReiniciar.set_sensitive(activo)
            self.opcionDetener.set_sensitive(activo)
        return True

    def iniciar(self) -> None:
        systemctl("import-environment", *VARIABLES_SESION)
        systemctl("reset-failed", SERVICIO)
        systemctl("start", "--no-block", SERVICIO)
        self.actualizar()

    def reiniciar(self) -> None:
        systemctl("import-environment", *VARIABLES_SESION)
        systemctl("restart", "--no-block", SERVICIO)
        self.actualizar()

    def detener(self) -> None:
        systemctl("stop", SERVICIO)
        self.actualizar()

    def abrirGUI(self) -> None:
        subprocess.Popen([self.ejecutable, "abrir-gui"])

    def verLogs(self) -> None:
        subprocess.Popen(["x-terminal-emulator", "-e", "journalctl", "--user", "-u", SERVICIO, "-f"])

    def salir(self) -> None:
        self.detener()
        self.quit()


if __name__ == "__main__":
    bandeja(sys.argv[1] if len(sys.argv) > 1 else "elgarrobo").run([])
