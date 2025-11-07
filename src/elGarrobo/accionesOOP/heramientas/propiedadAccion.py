from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .valoresAccion import valoresAcciones


@dataclass
class propiedadAccion:
    """
    clase de las propiedad de una acción de los atributos que se necesitan
    """

    nombre: str
    atributo: str
    tipo: list[str] | str = field(default_factory=list)
    obligatorio: bool = False
    descripcion: str = None
    ejemplo: str = None
    defecto: Optional[Any] = None

    def __post_init__(self) -> None:
        # Normalizar tipo a lista de tipos
        if not isinstance(self.tipo, list):
            self.tipo = [self.tipo] if self.tipo is not None else []

    def mismoTipo(self, valor: Any) -> bool:
        """Verifica si el tipo del valor coincide con el tipo de la propiedad

        Args:
            valor (Any): El valor a verificar
        Returns:
            bool: True si el tipo coincide, False en caso contrario
        """
        if not self.tipo:
            return True  # Acepta cualquier tipo si no se especifica ninguno
        for tipoActual in self.tipo:
            try:
                if isinstance(valor, tipoActual):
                    return True
            except TypeError:
                # tipoActual no es válido para isinstance(), ignorar
                continue
        return False

    def mismoAtributo(self, atributo) -> bool:
        """Verifica si el atributo coincide con el de la propiedad

        Args:
            atributo (str | valoresAcciones): El atributo a verificar
        Returns:
            bool: True si el atributo coincide, False en caso contrario
        """
        if isinstance(atributo, valoresAcciones):
            return atributo.atributo == self.atributo
        return atributo == self.atributo

    def __eq__(self, propiedad: object) -> bool:
        if isinstance(propiedad, valoresAcciones):
            return propiedad.atributo == self.atributo
        if isinstance(propiedad, propiedadAccion):
            return self.atributo == propiedad.atributo
        return NotImplemented

    def __str__(self) -> str:
        obligatorio: str = "*" if self.obligatorio else ""
        tipos = ", ".join(getattr(t, "__name__", str(t)) for t in self.tipo) if self.tipo else "Any"
        return f"Propiedad: {self.nombre}'{self.atributo}'[{tipos}]{obligatorio}"
