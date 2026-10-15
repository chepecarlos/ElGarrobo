# Mejoras pendientes

## Dibujo de botones

- [ ] **Editor de apariencia**: agregar más campos además de título, tópico MQTT y fondo: `imagen`, color del título, rotar, tamaño de fuente (`titulo_opciones`).
- [ ] **Vista previa en el editor con deck combinado**: usa siempre el primer StreamDeck (tamaño y rotación); debería usar el StreamDeck al que pertenece la tecla.

## Deck combinado / StreamDeck

- [ ] **Numeración estable**: `baseTeclas` se calcula al conectar con los botones de los StreamDeck conectados. Si uno está desconectado, el otro empieza en 1 y ejecuta acciones ajenas (y la cuadrícula de la GUI se solapa). Reservar siempre los botones de cada StreamDeck (ej. 15).
- [ ] **Layout sin conectar**: un StreamDeck desconectado se dibuja con `layoutDefecto` (Original 3x5, Plus 2x4); un Mini o XL desconectado sale mal. Podría guardarse el layout en `deck_combinado.md`.
- [ ] **`baseDial` en `MiDeckCombinado.conectar`**: usa `hasattr(baseActual, "cantidadDial")` sobre el int en vez del deck, así que nunca asigna `baseDial`. Hoy no se nota porque las perillas usan `dial_N` sin base; corregir o quitar si no hace falta.

### StreamDeck Plus

- [ ] **Toque largo en la pantalla**: `TouchscreenEventType.LONG` solo hace `print`, no busca acción.
- [ ] **Zonas no consecutivas**: el aparato divide la pantalla por la cantidad de `touchscreen_N` y busca tocar/deslizar por posición; con `touchscreen_1` y `touchscreen_3` la segunda zona busca `touchscreen_2`. Validar en la GUI o buscar por la clave real.

## GUI

- [ ] **Editor de pasos de macros**: ya hay un diálogo de bloques (agregar, editar, borrar, subir/bajar). Falta: arrastrar para ordenar, `macro_opciones` (cajón) sin YAML (hoy se conserva pero solo se edita en el YAML de la macro) y macros anidadas (un paso macro se edita en YAML).
- [ ] **Selector de acciones agrupado**: más de 37 acciones en una lista plana; agrupar por categoría (OBS, teclado, sonido, MQTT, folders...).
- [ ] **Deshacer más allá de borrar**: borrar ya tiene Deshacer en el aviso; editar, intercambiar y duplicar todavía no.
- [ ] **Atajos de teclado y edición en lote**: no hay atajos (guardar, limpiar, cambiar modo) ni forma de mover o borrar varias acciones a la vez.
- [ ] **Accesibilidad**: ordenar la lista solo con el mouse; mucho texto en `text-xs`; revisar contraste de los enlaces del pie (Youtube/TikTok sobre teal oscuro).
- [ ] **Alturas fijas en `vh`**: la cabecera (5vh) y el área de acciones (75vh / `calc(95vh - ...)`) quedan mal en ventanas bajas.

## Código

- [ ] **Interfaz tipo dict de `dataAccion`** (`get`, `[]`, `in`, `items`): quitarla cuando los dispositivos usen los campos directamente (marcada con `ponytail:` en `dataAccion.py`).
- [ ] **`folderActual` inicial `None`**: `rutaFolder` arma la ruta relativa con `str(self.folderActual)`, así que antes de cargar la raíz un folder relativo se busca en `None/<folder>`; en la app no pasa porque siempre se carga la raíz primero.

### Limpieza (auditoría de sobre-ingeniería)

Ordenado de mayor a menor recorte.

- [ ] **`src/configurar/` + flag `-c/--configurar`**: lee `modulos/configurar.json` y `modulos.json`, pero la config actual es `modulos.md` / `dispositivos.md`. Borrar el paquete y la opción en `main.py` si ya no se usa (incluye la clase `color` con códigos ANSI).
- [ ] **Paquete legacy `acciones/`** (~396 líneas, ~20 comentadas en `CargarAcciones()`): sí se importa en `elGarrobo.py:8` y aporta `pegar`, `portapapeles`, `textovoz`, `contrain`, `concatenar`, `asignar`, `escribir_valor(es)`, `ventana_texto`. Migrar a OOP solo los que se usan y borrar el resto (se van `pyttsx3` y `pyperclip`). Corregir la nota del CLAUDE.md que dice que no se importa.
- [ ] **Métodos sin llamadas en `elGarrobo.py`**: `CargarAcciones(self, Dispositivo, Data)`, `LimpiarDeck` y `BuscarDentroFolder` (solo se llama a sí mismo).
- [ ] **`ModuloMQTTEstado` + `modulos/mqtt_estado.py`**: el flag nunca se lee y el módulo es un stub (`EnviarAccionMQTT(): pass`). Borrar.
- [ ] **Código comentado**: bloque `ModuloGui`/`agregarAcciones` y `cargarFolder` en `IniciarAcciones`; ~65 líneas comentadas en `migui.py` y ~49 en `elGarrobo.py`. Git guarda la historia.
- [ ] **`cargarClasesModulos`**: la rama `else` para instancias y el `moduloInstancia = moduloClase` después de `continue` no se ejecutan nunca; `cargarModulos()` solo devuelve clases.
- [ ] **Dependencias sin usar en `requirements.txt`**: `pydub`, `importlib-resources`. Además `pyperclip` se importa en `acciones/emular_teclado.py` pero falta en `requirements.txt`.
- [ ] **`modulo.obtenerValor`**: sin llamadas (los módulos leen dicts) y duplica `elGarrobo.obtenerValor`. Borrar.
- [ ] **Flags `ModuloX` en `elGarrobo.py:140-163`**: se inicializan en `False` y se reasignan con `.get(..., False)`. Asignar una sola vez o leer `self.modulos`/`self.dispositivos` donde se usan. Revisar si `ModuloOBSNotificacion` y `ModuloMonitorESP` siguen haciendo falta.
- [ ] **`cargarDispositivos()` / `cargarModulos()`**: funciones que solo devuelven una lista literal; cambiar por constantes `DISPOSITIVOS = [...]` / `MODULOS = [...]`.

## Ortografía (requiere actualizar configs del usuario)

- [ ] Claves de macro `solisita` / `solisita_cambiar` → `solicita` / `solicita_cambiar` (ver CLAUDE.md).

## Configs del usuario (`~/dotfile/.config/elgarrobo/default/`)

- [ ] Imágenes que no existen: `freecad/geometria/linea.png`, `freecad/restricciones/distancia.png`, `inkscape/duplicar.png`.
- [x] `plus.md`: nombres "Uso Ran" → "Uso RAM" y "humedad Estudio" → "Humedad Estudio".
