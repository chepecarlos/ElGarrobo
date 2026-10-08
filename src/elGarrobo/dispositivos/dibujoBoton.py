"""Dibuja la imagen de un botón (fondo, imagen y título) a partir de su acción.

Lo usan el StreamDeck para mandar la imagen a la tecla y la GUI para la vista previa.
"""

import os
import re
from functools import cache
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as ImageImage

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerValor, leerData

logger = ConfigurarLogging(__name__)


@cache
def fuenteConfig() -> str | None:
    """'fuente' de config.md del usuario, se lee una vez"""
    # ponytail: cacheada, si se cambia la fuente en config.md hay que reiniciar
    return (leerData("config") or {}).get("fuente")


@dataclass
class dibujoBoton:
    """Datos del dispositivo y del folder que se necesitan para dibujar un botón"""

    folderPerfil: Path
    "Folder del perfil, base de las rutas de imágenes que empiezan con /"
    folderActual: Path = Path("/")
    "Folder actual dentro del perfil, base de las rutas de imágenes relativas"
    archivoFuente: str | None = None
    "Fuente para el título, si no hay se usa 'fuente' de config.md y si tampoco la de Pillow"
    propiedadFolder: Any = None
    "Acción 'propiedad_folder' del folder, sus opciones son el valor por defecto de los botones"
    imagenesBase: dict = field(default_factory=dict)
    "Imagen por defecto según el comando de la acción"
    rotar: int = 0
    "Rotación por defecto del dispositivo"

    patronTitulo = re.compile(r"(?<!{){[^{}]*}(?!})")
    "Patrón para detectar campos de formato en el título, evitando los dobles {{}} usados para escapar llaves en formato."

    def dibujar(self, accion, tamaño: tuple[int, int], conGif: bool = False, compensarRotar: int = 0) -> ImageImage | None:
        """Imagen completa del botón: fondo, imagen, título y rotación

        Args:
            accion: Datos de la acción del botón
            tamaño: ancho y alto del botón en pixeles
            conGif: si es False y la imagen es gif devuelve None (el StreamDeck la anima aparte),
                si es True dibuja el primer cuadro
            compensarRotar: grados que está rotado el aparato; la GUI lo usa para mostrar el ícono como lo ve el usuario

        Returns:
            ImageImage | None: imagen del botón
        """
        colorFondo: str = "black"

        opcionesFolder = (self.propiedadFolder or {}).get("imagen_opciones") or {}
        opciones = accion.get("imagen_opciones") or {}

        if "fondo" in opciones:
            colorFondo = opciones["fondo"]
        elif "fondo" in opcionesFolder:
            colorFondo = opcionesFolder.get("fondo")

        if "rotar" in opciones:
            rotar = opciones.get("rotar")
        elif "rotar" in opcionesFolder:
            rotar = opcionesFolder.get("rotar")
        else:
            rotar = self.rotar

        imagen: ImageImage = Image.new("RGB", tuple(tamaño), colorFondo)
        imagen = self.obtenerImagen(imagen, accion, conGif)
        if imagen is None:
            return None
        return imagen.rotate(rotar - compensarRotar, resample=Image.BICUBIC, expand=False)

    def obtenerPropiedad(self, accion, key: str, default=None) -> Any:
        """Busca una propiedad anidada con "/" (ej: "titulo_opciones/color"), primero en la acción y luego en el folder"""
        for datos in (accion, self.propiedadFolder):
            valor = datos
            for clave in key.split("/"):
                valor = valor.get(clave) if hasattr(valor, "get") else None
            if valor is not None:
                return valor
        return default

    def fuente(self, tamaño: int) -> ImageFont.FreeTypeFont:
        archivo = self.archivoFuente or fuenteConfig()
        if archivo:
            return ImageFont.truetype(archivo, size=tamaño)
        return ImageFont.load_default(size=tamaño)

    def obtenerImagen(self, imagen: ImageImage, accion, conGif: bool = False) -> ImageImage | None:
        imagenFondo = None

        if "imagen_opciones" in accion:
            opciones = accion["imagen_opciones"]
            if "imagen" in opciones:
                imagenFondo = opciones["imagen"]

        if imagenFondo is not None:
            self.ponerImagen(imagen, imagenFondo, accion, True)

        direccionImagen: str = self.buscarDireccionImagen(accion)

        if direccionImagen is not None and direccionImagen.endswith(".gif") and not conGif:
            return None

        self.ponerImagen(imagen, direccionImagen, accion)

        tituloBoton: str = self.buscarTitulo(accion)

        # Sin título ni imagen el botón quedaría vacío: se muestra el nombre
        if not tituloBoton and direccionImagen is None and imagenFondo is None:
            tituloBoton = accion.get("nombre")

        if tituloBoton is not None:
            self.ponerTexto(imagen, tituloBoton, accion, isinstance(direccionImagen, str))

        return imagen

    def buscarTitulo(self, accion) -> str | None:
        """Busca el título para el botón

        Args:
            accion: Datos de la acción del botón

        Returns:
            str | None: Título encontrado o None
        """

        titulo: str | None = None

        TextoCargar = accion.get("cargar_titulo")
        if TextoCargar is not None:
            archivoTexto = TextoCargar.get("archivo")
            atributoTexto = TextoCargar.get("atributo")
            if archivoTexto is not None and atributoTexto is not None:
                titulo = ObtenerValor(archivoTexto, atributoTexto)
                return titulo

        tituloValor = accion.get("titulo")
        titulo = str(tituloValor) if tituloValor is not None else None

        opciones: dict = accion.get("titulo_opciones", dict())
        if opciones is None:
            opciones = dict()

        topicTituloMQTT: str = opciones.get("mqtt", False)

        if topicTituloMQTT and isinstance(topicTituloMQTT, str):
            datoTituloMQTT = self.obtenerTituloMQTT(topicTituloMQTT, titulo)

            if titulo is not None and self.patronTitulo.search(titulo):
                try:
                    titulo = titulo.format(datoTituloMQTT)
                except (ValueError, TypeError):
                    # Soporta formatos numéricos como {:.2f} cuando llega texto por MQTT.
                    valorFormateable = datoTituloMQTT
                    if isinstance(datoTituloMQTT, str):
                        datoNormalizado = datoTituloMQTT.strip().replace(",", ".")
                        try:
                            valorFormateable = float(datoNormalizado)
                        except ValueError:
                            valorFormateable = datoTituloMQTT

                    try:
                        titulo = titulo.format(valorFormateable)
                    except (ValueError, TypeError, IndexError, KeyError):
                        titulo = str(datoTituloMQTT)
            else:
                titulo = datoTituloMQTT

        if isinstance(titulo, str):
            titulo = titulo.strip()

        return titulo

    def calcularRutaImagen(self, rutaImagen: str) -> str:
        """Calcula la Ruta absoluta de imagen

        Args:
            rutaImagen (str): ruta relativa de la imagen

        Returns:
            str: ruta absoluta de la imagen
        """

        pathImagen = Path(rutaImagen)

        if rutaImagen.startswith("/"):
            pathImagen = self.folderPerfil / rutaImagen.lstrip("/")
        else:
            pathImagen = self.folderPerfil / str(self.folderActual).lstrip("/") / pathImagen

        return str(pathImagen.resolve())

    def ponerImagen(self, Imagen: ImageImage, NombreIcono: str, accion, fondo: bool = False):
        if NombreIcono is None:
            return

        DireccionIcono = self.calcularRutaImagen(NombreIcono)

        if os.path.exists(DireccionIcono):
            Icono = Image.open(DireccionIcono).convert("RGBA")
            if "titulo" in accion and not fondo:
                Icono.thumbnail((Imagen.width, Imagen.height - 20), Image.LANCZOS)
            else:
                Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)
        else:
            logger.warning(f"Deck[No Imagen] {NombreIcono} - {DireccionIcono}")
            Icono = Image.new(mode="RGBA", size=(256, 256), color=(153, 153, 255))
            Icono.thumbnail((Imagen.width, Imagen.height), Image.LANCZOS)

        IconoPosicion = ((Imagen.width - Icono.width) // 2, 0)
        Imagen.paste(Icono, IconoPosicion, Icono)

    def ponerTexto(self, Imagen, titulo: str, accion, hayImagen: bool = False, cortePalabra: bool = False):
        """Agrega Texto a Botones de StreamDeck.

        Args:
            Imagen (Image): Imagen del botón
            accion: Datos de la acción del botón
            hayImagen (bool, optional): Si ya tiene imagen el botón. Defaults to False.
        """

        TituloInicial: str = titulo

        tamañoFuenteMáximo: int | None = self.obtenerPropiedad(accion, "titulo_opciones/tamanno_maximo")
        tamañoFuenteMínimo: int | None = self.obtenerPropiedad(accion, "titulo_opciones/tamanno_minimo")
        alinear: str | None = self.obtenerPropiedad(accion, "titulo_opciones/alinear")
        Borde_Color: str = self.obtenerPropiedad(accion, "titulo_opciones/borde_color", "black")
        Borde_Grosor: int = self.obtenerPropiedad(accion, "titulo_opciones/borde_grosor", 6)
        Titulo_Color: str = self.obtenerPropiedad(accion, "titulo_opciones/color", "white")

        Lineas = TituloInicial.split("\\n")
        titulo = "\n".join(Lineas)
        if cortePalabra:
            Lineas = titulo.split(" ")
            titulo = "\n".join(Lineas)

        titulo = titulo.replace("⁰", "°")

        espacioLinea: int = 1

        dibujo: ImageDraw = ImageDraw.Draw(Imagen)

        if hayImagen:
            alinear = alinear or "abajo"

        tamañoFuente, altoTitulo, anchoTitulo = self.calcularTamañoFuente(
            Imagen,
            titulo,
            Borde_Grosor,
            espacioLinea,
            minimo=tamañoFuenteMínimo,
            maximo=tamañoFuenteMáximo,
        )

        fuente = self.fuente(tamañoFuente)

        textoX = (Imagen.width - anchoTitulo) / 2 + Borde_Grosor

        if alinear == "abajo":
            textoY = Imagen.height - altoTitulo
        elif alinear == "arriba":
            textoY = 0
        else:  # centro
            textoY = (Imagen.height - altoTitulo) / 2

        posicionTexto = (textoX, textoY)

        dibujo.multiline_text(
            posicionTexto,
            text=titulo,
            font=fuente,
            fill=Titulo_Color,
            stroke_width=Borde_Grosor,
            stroke_fill=Borde_Color,
            align="center",
            spacing=espacioLinea,
        )

    def calcularTamañoFuente(self, imagen: ImageImage, texto: str, grosorBorde: int, espacioLinea: int, minimo: int | None, maximo: int | None = None) -> tuple[int, int, int]:
        """Calcula tamaño de fuente para texto en botón de StreamDeck.

        Args:
            imagen (ImageImage): Imagen del botón
            texto (str): Texto a colocar en el botón
            grosorBorde (int): Grosor del borde del texto
            espacioLinea (int): Espacio entre líneas del texto
            minimo (int | None): Tamaño mínimo de fuente
            maximo (int | None): Tamaño máximo de fuente

        Returns:
            tuple[int, int, int]: Tamaño de fuente, alto del texto y ancho del texto
        """

        anchoImagen, altoImagen = imagen.width, imagen.height
        dibujo = ImageDraw.Draw(imagen)

        def medir(tamaño: int) -> tuple[int, int]:
            caja = dibujo.multiline_textbbox(xy=[0, 0], text=texto, font=self.fuente(tamaño), align="center", spacing=espacioLinea, stroke_width=grosorBorde)
            return caja[2] - caja[0], caja[3] - caja[1]

        anchoTitulo, altoTitulo = medir(100)
        # La escala lineal se pasa porque el borde no crece con la fuente, se baja de 1 en 1 hasta que quepa
        tamañoFuente = max(3, int(100 * min(anchoImagen / anchoTitulo, altoImagen / altoTitulo)))
        while tamañoFuente > 3:
            anchoTitulo, altoTitulo = medir(tamañoFuente)
            if anchoTitulo <= anchoImagen and altoTitulo <= altoImagen:
                break
            tamañoFuente -= 1

        if minimo is not None and tamañoFuente < minimo:
            tamañoFuente = minimo

        if maximo is not None and tamañoFuente > maximo:
            tamañoFuente = maximo

        anchoTitulo, altoTitulo = medir(tamañoFuente)

        return tamañoFuente, altoTitulo, anchoTitulo

    def buscarDireccionImagen(self, accion) -> str | None:
        """Busca la dirección de imagen

        Args:
            accion: Datos de la acción del botón
        """

        if "imagen_estado" in accion:

            imagenEstado = accion.get("imagen_estado")
            nombreAccion = accion.get("accion")
            opcionesAccion = accion.get("opciones")

            if nombreAccion.startswith("obs"):
                estadoImagen = self.BuscarImagenOBS(nombreAccion, opcionesAccion)
                if estadoImagen:
                    DireccionImagen = imagenEstado.get("imagen_true")
                else:
                    DireccionImagen = imagenEstado.get("imagen_false")

                return DireccionImagen

        if "imagen" in accion:
            DireccionImagen = accion.get("imagen")
            return DireccionImagen
        elif "accion" in accion:
            nombreAccion = accion.get("accion")
            if nombreAccion in self.imagenesBase:
                return self.imagenesBase[nombreAccion]

        return None

    @staticmethod
    def BuscarImagenOBS(NombreAccion: str, opcionesAccion: dict) -> bool | None:
        Estado = None

        ListaBasicas = ["obs_conectar", "obs_grabar", "obs_pausar", "obs_envivo", "obs_camara_virtual", "obs_grabar_vertical"]
        for Basica in ListaBasicas:
            if NombreAccion == Basica:
                Estado = ObtenerValor("data/obs/obs", Basica)

        if NombreAccion == "obs_escena":
            if "escena" in opcionesAccion:
                EscenaActual = opcionesAccion["escena"]
                EscenaActiva = ObtenerValor("data/obs/obs", "obs_escena")
                if EscenaActual == EscenaActiva:
                    Estado = True
                else:
                    Estado = False
        elif NombreAccion == "obs_fuente":
            if "fuente" in opcionesAccion:
                FuenteActual = opcionesAccion["fuente"]
                Estado = ObtenerValor("data/obs/obs_fuente", FuenteActual)
        elif NombreAccion == "obs_filtro":
            if "fuente" in opcionesAccion:
                Fuente = opcionesAccion["fuente"]
            if "filtro" in opcionesAccion:
                Filtro = opcionesAccion["filtro"]
            if Fuente is not None and Filtro is not None:
                Estado = ObtenerValor("data/obs/obs_filtro", [Fuente, Filtro])

        if Estado is None:
            Estado = False

        return Estado

    @staticmethod
    def obtenerTituloMQTT(topicTitulo: str, tituloInicial: str = "") -> str:
        """Obtiene el titulo enviado por MQTT

        Args:
            topicTitulo (str): Cual topic hay que leer
            tituloInicial (str): Titulo inicial si no se encuentra el topic

        Returns:
            str: devuelve el titulo encontrado
        """

        archivoTituloMQTT: str = "data/tituloMQTT"

        titulo = ObtenerValor(archivoTituloMQTT, topicTitulo)
        if titulo is None:
            return tituloInicial
        return titulo


if __name__ == "__main__":
    import tempfile

    from elGarrobo.dispositivos.dataAccion import dataAccion

    with tempfile.TemporaryDirectory() as carpeta:
        dibujo = dibujoBoton(folderPerfil=Path(carpeta))
        acción = dataAccion(titulo="Hola")
        acción.fondo = "#ff0000"
        imagen = dibujo.dibujar(acción, (72, 72))
        assert imagen.size == (72, 72) and imagen.getpixel((1, 1)) == (255, 0, 0)

        # el fondo del folder aplica si el botón no tiene
        dibujo.propiedadFolder = dataAccion(imagenOpciones={"fondo": "#00ff00"}, tituloOpciones={"color": "blue"})
        assert dibujo.dibujar(dataAccion(), (72, 72)).getpixel((1, 1)) == (0, 255, 0)
        assert dibujo.obtenerPropiedad(dataAccion(), "titulo_opciones/color") == "blue"

        # gif: None para el StreamDeck, primer cuadro para la vista previa
        Image.new("RGB", (10, 10), "white").save(Path(carpeta) / "a.gif")
        assert dibujo.dibujar(dataAccion(imagen="a.gif"), (72, 72)) is None
        assert dibujo.dibujar(dataAccion(imagen="a.gif"), (72, 72), conGif=True) is not None

        # el título cabe a lo ancho contando el borde, salvo que el usuario pida un mínimo mayor
        _, _, ancho = dibujo.calcularTamañoFuente(Image.new("RGB", (72, 72)), "Sequencer", 6, 1, minimo=None)
        assert ancho <= 72
        tamaño, _, _ = dibujo.calcularTamañoFuente(Image.new("RGB", (72, 72)), "texto muy largo", 6, 1, minimo=20)
        assert tamaño == 20
        # sin título ni imagen se usa el nombre; con título o imagen no
        assert dibujo.dibujar(dataAccion(nombre="Casa OS"), (72, 72)).tobytes() != dibujo.dibujar(dataAccion(), (72, 72)).tobytes()
        assert dibujo.dibujar(dataAccion(nombre="A", titulo="B"), (72, 72)).tobytes() == dibujo.dibujar(dataAccion(nombre="X", titulo="B"), (72, 72)).tobytes()
    print("ok")
