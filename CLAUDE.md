# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is ElGarrobo

ElGarrobo es una herramienta de macros para Linux compatible con StreamDeck, teclados USB, MQTT y OBS WebSocket. Mapea teclas físicas a acciones configuradas en archivos `.md`/`.json` del usuario.

## Commands

```bash
# Instalar con pipx (recomendado)
make install
make uninstall      # desinstalar de pipx
make install-dev    # instalar editable en venv/ con dependencias de test (pip)

# Ejecutar tests
make test
pytest tests/test_tool.py -v    # un solo archivo de test

# Tests con cobertura
make test-cov
make test-cov-html

# Documentación (pdoc)
make docs
make serve-docs

# Dependencias del sistema
make extras

# Ejecutar después de instalar
elgarrobo           # modo normal
elgarrobo -d        # con depuración
elgarrobo -g        # con GUI
elgarrobo -c        # modo configuración interactiva
```

El formateador de código es **Black** con `line-length = 119`.

## Arquitectura

### Flujo principal

`main.py` → `elGarrobo` (clase orquestadora) → carga módulos → carga dispositivos → espera eventos → ejecuta acciones.

### Tres pilares

**1. Acciones** (`src/elGarrobo/accionesOOP/`)

Heredan de `accion` (clase base en `accion.py`). Cada acción define:
- `nombre`, `comando` (string clave), `descripcion`
- `listaPropiedades`: lista de `propiedadAccion` con nombre, tipo y si es obligatoria. Para propiedades `str` de varias líneas (ej. `texto` en `accionEscribirTexto`) usar `multilinea=True` para que la GUI muestre un `textarea` en vez de un `input`
- `configurar(dict)` → valida y llena `listaValores`
- `ejecutar()` → verifica propiedades y llama a `funcion` o `funcionExterna`

Las acciones se registran en `cargarClasesAcciones()` como dict `{comando: ClaseAccion}`. Para crear una acción nueva: heredar de `accion`, agregar propiedades en `__init__`, implementar `ejecutar()`, y registrarla en ese dict.

Algunas acciones (como `accionSalir`, `accionEntrarFolder`) reciben su lógica mediante `funcionExterna` inyectada desde `elGarrobo.py`, porque requieren acceso al estado central.

**2. Dispositivos** (`src/elGarrobo/dispositivos/`)

Heredan de `dispositivo` (clase base en `dispositivo.py`). Leen archivos de configuración `.md` o `.json` desde el folder de perfil del usuario (`ObtenerFolderConfig()/<perfil>/`). Cuando el usuario presiona una tecla, llaman a `ejecutarAcción(accionData, estado, fuerza)` que elGarrobo inyecta en `configurarFuncionAccion()`.

Dispositivos disponibles: `MiTecladoMacro`, `MiPedal`, `MiDeckCombinado`, `MiMQTT`, `miGui`.

Los dispositivos soportan navegación por folders jerárquicos; `cargarAccionesFolder(path)` carga el archivo de acciones del folder dado.

**3. Módulos** (`src/elGarrobo/modulos/`)

Integraciones de fondo (OBS, estado PC, Octoprint, MQTT estado). Heredan de `modulo`. Se activan desde `modulos.md` en el config del usuario. `cargarModulos()` los descubre y `elGarrobo.cargarClasesModulos()` los instancia y ejecuta si están habilitados.

### Configuración del usuario

Los archivos de configuración son `.md` con frontmatter YAML o `.json`. Viven en el folder devuelto por `miLibrerias.ObtenerFolderConfig()`. El archivo `modulos.md` es el punto de entrada: habilita/deshabilita cada dispositivo y módulo.

Cada dispositivo tiene su propio archivo de acciones. Cada entrada de acción tiene al menos `key` y `accion`, más un dict opcional `opciones` con los parámetros de la acción.

### Macros

Las macros encadenan acciones secuencialmente. El "cajón" (`cajon: dict`) pasa datos entre pasos: `macro_opciones.solisita` extrae un valor del cajón y `macro_opciones.respuesta` guarda el resultado de una acción para el siguiente paso.

### Submodulo miLibrerias

`src/elGarrobo/miLibrerias/` es un submódulo git. Provee funciones de logging (`ConfigurarLogging`), lectura/escritura de archivos `.md`/`.json` (`ObtenerArchivo`, `SalvarArchivo`, `leerData`), y utilidades de config (`ObtenerFolderConfig`, `obtenerArchivoPaquete`).

## Limpieza de ortografía (en curso)

El código tiene bastantes errores de ortografía en español (nombres de clases, docstrings, descripciones, y algunas claves `comando`/opciones de config). Cuando Claude detecte uno, debe avisarlo para corregirlo poco a poco.

- **Seguro de corregir de inmediato**: docstrings, comentarios, `descripcion`, nombres de variables/métodos internos que no se serializan a los `.md`/`.json` del usuario.
- **Requiere confirmación antes de tocar**: cualquier string usado como clave persistida en configs de usuario — el `comando` de una acción (clave del dict en `cargarClasesAcciones()`), o claves dentro de `opciones`/`macro_opciones` (ver `solisitaMacro` en `elGarrobo.py`). Cambiarlas rompe macros ya guardadas por el usuario.

Pendientes detectados (no corregidos, requieren decidir si romper compatibilidad):
- `elGarrobo.py` (`solisitaMacro`): claves de macro `"solisita"` / `"solisita_cambiar"` → deberían ser `"solicita"` / `"solicita_cambiar"`.
- `src/elGarrobo/acciones/` (paquete legacy no-OOP, no se importa desde ningún lado): mismos typos, ignorado porque parece código muerto.

Corregidos (código + configs de usuario en `~/dotfile/.config/elgarrobo/default/*.md` actualizados en el mismo cambio):
- `accionSonidos.py`: `comando = "reproducion"` / `"detener_reproducion"` → `"reproduccion"` / `"detener_reproduccion"`.
