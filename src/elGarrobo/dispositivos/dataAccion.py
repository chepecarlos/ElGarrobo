from dataclasses import dataclass, field, fields
from typing import Any

from elGarrobo.accionesOOP.herramientas.propiedadAccion import propiedadAccion


def campo(clave: str = None, gui: propiedadAccion = None, **kwargs) -> Any:
    """Campo de dataAccion con metadata

    Args:
        clave (str, optional): clave en el .md/.json si es distinta al nombre de la variable
        gui (propiedadAccion, optional): si se indica, el usuario lo puede editar en la GUI
    """
    metadata = {}
    if clave:
        metadata["clave"] = clave
    if gui:
        metadata["gui"] = gui
    return field(metadata=metadata, **kwargs)


@dataclass
class dataAccion:
    """Una entrada de acción tal como está en el .md/.json del usuario.

    Por defecto la clave en el archivo es el nombre del campo; si es distinta se indica con campo(clave="...").
    Los campos con campo(gui=propiedadAccion(...)) aparecen en el formulario de la GUI, en este orden.
    """

    nombre: str = campo(gui=propiedadAccion(nombre="Nombre", atributo="nombre", obligatorio=True), default=None)
    titulo: str = None
    "Texto del botón, se edita en el editor del botón de la GUI"
    key: str = campo(gui=propiedadAccion(nombre="Tecla", atributo="key", obligatorio=True), default=None)
    descripcion: str = campo(
        gui=propiedadAccion(
            nombre="Descripción",
            atributo="descripcion",
            descripcion="Nota para recordar qué hace esta acción",
            multilinea=True,
        ),
        default=None,
    )
    accion: str = None
    opciones: dict = field(default_factory=dict)
    imagen: str = None
    imagenOpciones: dict = campo("imagen_opciones", default_factory=dict)
    tituloOpciones: dict = campo("titulo_opciones", default_factory=dict)
    extra: dict = field(default_factory=dict)
    "Claves del archivo que no tienen campo, se guardan aquí para no perderlas al salvar"

    @staticmethod
    def claveArchivo(campo) -> str:
        return campo.metadata.get("clave", campo.name)

    @property
    def fondo(self) -> str | None:
        """Color de fondo del botón, en el .md vive en imagen_opciones.fondo"""
        return self.imagenOpciones.get("fondo")

    @fondo.setter
    def fondo(self, color: str | None) -> None:
        if color:
            self.imagenOpciones["fondo"] = color
        else:
            self.imagenOpciones.pop("fondo", None)

    @classmethod
    def propiedadesGui(cls) -> list[propiedadAccion]:
        """Propiedades que el usuario puede editar en la GUI, su atributo es la clave en el .md"""
        return [f.metadata["gui"] for f in fields(cls) if "gui" in f.metadata]

    @classmethod
    def desdeDict(cls, data: dict) -> "dataAccion":
        data = dict(data)
        valores = {
            f.name: data.pop(cls.claveArchivo(f))
            for f in fields(cls)
            if f.name != "extra" and cls.claveArchivo(f) in data
        }
        return cls(**valores, extra=data)

    def aDict(self) -> dict:
        """Dict listo para salvar en el .md/.json, sin los campos vacíos"""
        data = {self.claveArchivo(f): getattr(self, f.name) for f in fields(self) if f.name != "extra"}
        data = {k: v for k, v in data.items() if v not in (None, {}, [])}
        return {**data, **self.extra}

    # ponytail: interfaz tipo dict con las claves del .md para que el código viejo (acción.get("key"), acción["titulo"] = ...)
    # siga funcionando; quitarla cuando los dispositivos usen los campos directamente
    def _campo(self, claveMd: str) -> str | None:
        return next((f.name for f in fields(self) if f.name != "extra" and self.claveArchivo(f) == claveMd), None)

    def get(self, claveMd: str, defecto: Any = None) -> Any:
        return self.aDict().get(claveMd, defecto)

    def __getitem__(self, claveMd: str) -> Any:
        return self.aDict()[claveMd]

    def __setitem__(self, claveMd: str, valor: Any) -> None:
        campo = self._campo(claveMd)
        if campo is None:
            self.extra[claveMd] = valor
        else:
            setattr(self, campo, valor)

    def __contains__(self, claveMd: str) -> bool:
        return claveMd in self.aDict()

    def items(self):
        return self.aDict().items()


if __name__ == "__main__":
    original = {
        "nombre": "OBS",
        "key": "1",
        "accion": "obs_escena",
        "opciones": {"escena": "a"},
        "imagen_opciones": {"fondo": "red"},
        "macro_opciones": {"x": 1},
    }
    acción = dataAccion.desdeDict(original)
    assert acción.imagenOpciones == {"fondo": "red"}
    assert acción.extra == {"macro_opciones": {"x": 1}}
    assert acción.aDict() == original
    assert acción.get("imagen_opciones") == {"fondo": "red"} and "titulo" not in acción
    acción["titulo_opciones"] = {"mqtt": "t"}
    acción["__estado"] = True
    assert acción.tituloOpciones == {"mqtt": "t"} and acción.extra["__estado"] is True
    assert [p.atributo for p in dataAccion.propiedadesGui()] == ["nombre", "key", "descripcion"]
    acción.fondo = "#2b7a10"
    assert acción.aDict()["imagen_opciones"] == {"fondo": "#2b7a10"}
    acción.fondo = None
    assert "imagen_opciones" not in acción
    print("ok")
