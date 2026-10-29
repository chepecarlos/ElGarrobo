"""
## Módulo Base
- Clase que heredan todos los módulos: [modulo](./modulos/modulo)

Los módulos son integraciones de fondo. Se activan en `modulos.md` del folder de configuración
del usuario con su clave (ej. `obs: true`) y pueden agregar sus propias acciones,
que solo se registran si el módulo está activado.

# Lista de Módulos

| Módulo | Clave en `modulos.md` | Configuración | Acciones |
|---|---|---|---|
| [moduloOBS](./modulos/obs/moduloOBS) | `obs` | `modulos/audio_obs/`, `modulos/alerta_obs/` | [accionesOBS](./modulos/obs/accionesOBS) |
| [moduloOctoprint](./modulos/octoprint/moduloOctoprint) | `estado_octoprint` | `modulos/estado_octoprint.md` | [accionesOctoprint](./modulos/octoprint/accionesOctoprint) |
| [moduloKlipper](./modulos/klipper/moduloKlipper) | `estado_klipper` | `modulos/estado_klipper.md` | [accionesKlipper](./modulos/klipper/accionesKlipper) |
| [moduloFdmMonster](./modulos/fdmMonster/moduloFdmMonster) | `estado_fdm_monster` | `modulos/estado_fdm_monster.md` | [accionesFdmMonster](./modulos/fdmMonster/accionesFdmMonster) |
| [estadoPc](./modulos/estadoPc) | `estado_pc` | `modulos/estado_pc.md` | - |

Extras de OBS en `modulos.md`: `obs_notificacion` (notifica cambios de estado) y `obs_monitor_audio` (envía niveles de audio por MQTT).

# Crear un Módulo Nuevo
1. Crear la carpeta `modulos/<nombre>/` con un `__init__.py` vacío.
2. En `modulo<Nombre>.py` heredar de `modulo` y definir `nombre`, `modulo` (clave en `modulos.md`),
   `descripcion` y, si usa configuración, `archivoConfiguracion` y `propiedades` (lista de `propiedadAccion`).
   La GUI arma el formulario en /modulos con `propiedades`, así se puede configurar sin que exista el archivo;
   para listas como impresoras usar `tipo=[list]` y `elementos=[...]`.
3. El `__init__` no debe tener efectos (se instancia aunque esté apagado); iniciar todo en `ejecutar()`.
4. Si tiene acciones, crearlas en `acciones<Nombre>.py` heredando de `accion` y listarlas en `acciones = [...]`.
   Al registrarse reciben la instancia del módulo en el atributo de clase `modulo`.
5. Si avisa cosas (ej. una impresora terminó), declararlas en `eventos = [eventoModulo(nombre, descripcion, datos)]`
   y llamar `self.emitirEvento(nombre, datos)`; el usuario les asigna acciones en `eventos.md` o en /eventos.
6. Agregar la clase a `cargarModulos()`.
"""

from .estadoPc import estadoPc
from .modulo import modulo
from .octoprint.moduloOctoprint import moduloOctoprint
from .klipper.moduloKlipper import moduloKlipper
from .fdmMonster.moduloFdmMonster import moduloFdmMonster
from .obs.moduloOBS import moduloOBS


def cargarModulos() -> list[type["modulo"]]:
    """Función para cargar los módulos disponibles"""
    listaModulos: list[type["modulo"]] = [
        estadoPc,
        moduloOctoprint,
        moduloKlipper,
        moduloFdmMonster,
        moduloOBS,
    ]
    return listaModulos
