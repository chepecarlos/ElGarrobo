"""
Este es el Inicio del Código que llama a las funciones
"""

import threading
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from configurar.modulo import ConfigurarModulos
from elGarrobo import miLibrerias
from elGarrobo.elGarrobo import elGarrobo
from elGarrobo.dispositivos import cargarDispositivos
from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerFolderConfig, SalvarValor, leerData
from elGarrobo.modulos import cargarModulos

logger = ConfigurarLogging(__name__)

app = typer.Typer(
    help="Herramientas de Macros de ALSW",
    context_settings={"help_option_names": ["-h", "--help"]},
)
modulos_app = typer.Typer(help="Gestión de los módulos de ElGarrobo")
app.add_typer(modulos_app, name="modulos")
dispositivos_app = typer.Typer(help="Gestión de los dispositivos de ElGarrobo")
app.add_typer(dispositivos_app, name="dispositivos")


def _version_callback(valor: bool) -> None:
    if valor:
        typer.echo(miLibrerias.obtenerVersionPaquete())
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def _cli(
    ctx: typer.Context,
    configurar: Annotated[
        bool, typer.Option("--configurar", "-c", help="Sistema configuración del programa")
    ] = False,
    depuracion: Annotated[bool, typer.Option("--depuracion", "-d", help="Activa la depuración")] = False,
    gui: Annotated[bool, typer.Option("--gui", "-g", help="Sistema interface gráfica")] = False,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Version del programa"),
    ] = None,
) -> None:
    if ctx.invoked_subcommand is not None:
        return

    logger.info("ElGarrobo[Iniciando]")
    if depuracion:
        logger.info("ElGarrobo[Depuración Activa]")
        logger.setLevel("DEBUG")

    if configurar:
        ConfigurarModulos()
    elif gui:
        logger.info("Iniciando la APP Gráfica")
        app = elGarrobo(gui="true")
        _mantenerVivo(app)
    else:
        logger.info("ElGarrobo[sin parametros]")
        try:
            app = elGarrobo()
            _mantenerVivo(app)
        except Exception as error:
            logger.exception(f"Error Main[{error}]")


def _mantenerVivo(app: elGarrobo) -> None:
    """Bloquea el hilo principal para que los hilos de los dispositivos (GUI, teclado, mqtt, etc.)
    sigan corriendo. Sin esto, el hilo principal termina apenas se crea elGarrobo() y Python
    empieza a cerrar el interprete mientras esos hilos todavia estan arrancando.

    Al salir (Ctrl+C) llama a Salir(), que desconecta los dispositivos y mata el proceso.
    De lo contrario los hilos en segundo plano (teclado, deck, GUI) quedan vivos para siempre
    y el proceso nunca termina.
    """
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        logger.info("ElGarrobo[Saliendo]")
        app.Salir([])


def _mostrar_info(titulo: str, archivo: str, cargar_clases) -> None:
    configuracion = leerData(archivo) or {}

    tabla = Table(title=titulo)
    tabla.add_column("Nombre")
    tabla.add_column("Estado")
    tabla.add_column("Descripción")

    for clase in cargar_clases():
        clave = clase.modulo
        if clave not in configuracion:
            estado = "[yellow]No configurado[/yellow]"
        elif configuracion[clave]:
            estado = "[green]Activado[/green]"
        else:
            estado = "[red]Desactivado[/red]"
        tabla.add_row(clase.nombre, estado, clase.descripcion)

    Console().print(tabla)


def _buscar_clase(identificador: str, cargar_clases):
    identificador = identificador.lower()
    for clase in cargar_clases():
        if identificador in (clase.nombre.lower(), clase.modulo.lower()):
            return clase
    return None


def _cambiar_estado(archivo: str, cargar_clases, etiqueta: str, identificador: str, estado: bool) -> None:
    clase = _buscar_clase(identificador, cargar_clases)
    if clase is None:
        typer.echo(f"{etiqueta} '{identificador}' no encontrado", err=True)
        raise typer.Exit(1)

    SalvarValor(archivo, clase.modulo, estado)
    accion = "activado" if estado else "desactivado"
    typer.echo(f"{etiqueta} [{clase.nombre}] {accion}")


@modulos_app.command("info")
def modulos_info() -> None:
    """Muestra los módulos disponibles y su estado configurado en modulos.md."""
    _mostrar_info("Módulos de ElGarrobo", "modulos", cargarModulos)


@modulos_app.command("activar")
def modulos_activar(nombre: str) -> None:
    """Activa un módulo por su nombre o clave (ej: estadoPc, estado_pc)."""
    _cambiar_estado("modulos", cargarModulos, "Módulo", nombre, True)


@modulos_app.command("desactivar")
def modulos_desactivar(nombre: str) -> None:
    """Desactiva un módulo por su nombre o clave (ej: estadoPc, estado_pc)."""
    _cambiar_estado("modulos", cargarModulos, "Módulo", nombre, False)


@dispositivos_app.command("info")
def dispositivos_info() -> None:
    """Muestra los dispositivos disponibles y su estado configurado en dispositivos.md."""
    _mostrar_info("Dispositivos de ElGarrobo", "dispositivos", cargarDispositivos)


@dispositivos_app.command("activar")
def dispositivos_activar(nombre: str) -> None:
    """Activa un dispositivo por su nombre o clave (ej: teclado, mqtt, deck_combinado)."""
    _cambiar_estado("dispositivos", cargarDispositivos, "Dispositivo", nombre, True)


@dispositivos_app.command("desactivar")
def dispositivos_desactivar(nombre: str) -> None:
    """Desactiva un dispositivo por su nombre o clave (ej: teclado, mqtt, deck_combinado)."""
    _cambiar_estado("dispositivos", cargarDispositivos, "Dispositivo", nombre, False)


def configurar() -> None:
    folderConfig = ObtenerFolderConfig()
    print(folderConfig)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
