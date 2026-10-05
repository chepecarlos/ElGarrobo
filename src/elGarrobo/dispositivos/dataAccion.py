from dataclasses import dataclass, field, fields
from typing import Any


def clave(nombre: str, **kwargs) -> Any:
    """Campo cuya clave en el .md/.json es distinta al nombre de la variable"""
    return field(metadata={"clave": nombre}, **kwargs)


@dataclass
class dataAccion:
    """Una entrada de acción tal como está en el .md/.json del usuario.

    Por defecto la clave en el archivo es el nombre del campo; si es distinta se indica con clave("...").
    """

    nombre: str = None
    titulo: str = None
    key: str = None
    descripcion: str = None
    accion: str = None
    opciones: dict = field(default_factory=dict)
    imagen: str = None
    imagenOpciones: dict = clave("imagen_opciones", default_factory=dict)
    tituloOpciones: dict = clave("titulo_opciones", default_factory=dict)
    extra: dict = field(default_factory=dict)
    "Claves del archivo que no tienen campo, se guardan aquí para no perderlas al salvar"

    @staticmethod
    def claveArchivo(campo) -> str:
        return campo.metadata.get("clave", campo.name)

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
    print("ok")
