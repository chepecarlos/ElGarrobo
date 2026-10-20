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
- [ ] **Alturas fijas en `vh`**: la cabecera ya se mide sola (`--alto-cabecera`), pero el formulario (75vh) y las restas en px del área de acciones siguen siendo aproximadas.

### Auditoría técnica (2026-10-17, `/impeccable audit`: 11/20)

- [ ] **[P0] Varios clientes se pisan**: los widgets viven en `self` (`editoresData`, `pestañas`, `paneles`, `dispositivo.panel`), así que con dos pestañas abiertas (ej. celular + escritorio) el clic en una llena el formulario de la otra, la primera deja de redibujarse y Usar/Editar es global. Guardar el estado por cliente (objeto de vista creado en cada `@ui.page`) y que el dispositivo avise a todas las vistas.
- [ ] **[P0] GUI abierta a la red sin contraseña**: `ui.run` sin `host` escucha en `0.0.0.0` y `accionOS` corre `shell=True`; cualquiera en la red puede ejecutar comandos. `host="127.0.0.1"` por defecto y abrir a la red solo con opción en `gui.md` + token.
- [x] **[P1] Edición inválida deja la acción a medias** (`agregarAcción`): copia nombre/tecla/acción/apariencia a `accionEditar` antes de validar las opciones; si fallan, el objeto en `listaAcciones` ya cambió y el próximo `salvarAcciones()` lo escribe al `.md`. Validar con `leerOpciones` antes de tocar nada y cambiar `except Exception` por `except ValueError`.
- [x] **[P1] Contraste de colores por defecto de Quasar**: nunca se llama `ui.colors()`. Botones planos `negative` (Salir, Reiniciar, Descartar, borrar paso) dan 2.63:1; blanco sobre `primary` azul (Listo, Guardar) da 3.06:1; el foco de los campos subraya en azul fuera de la paleta. Hecho: `COLORES_QUASAR` (primary teal-700, negative `#dc2626`, positive `#15803d`); en campos, menús y botones planos `--q-primary` es el teal claro y los errores un rojo claro; las confirmaciones destructivas son botones rellenos.
- [ ] **[P1] Teclado en celular**: en modo Usar a 390px las 87 teclas miden 9.5px y las etiquetas se enciman. Scroll horizontal con tamaño mínimo o caer a `dibujarBotonera` con las teclas que tienen acción.
- [x] **[P2] Botones táctiles de 36px**: barra de herramientas, `+`, limpiar y menú; `pointer: coarse` solo agrandaba el interruptor Usar/Editar. Hecho: 44px para todo `q-btn` (menos las teclas) y `q-toggle` con `pointer: coarse`.
- [x] **[P2] Diálogo "Apariencia del botón" a 390px**: la fila `no-wrap` (`w-64` + `w-24`) mide 400px en una tarjeta de 342px y corta la vista previa.
- [x] **[P2] Sin encabezados `h1`–`h6`**: "ElGarrobo", "Módulos" y los títulos de diálogos son `div`. Hecho: `miGui.encabezado` agrega `role=heading` y `aria-level`.
- [x] **[P2] Foco poco visible en botones Quasar** (solo el tinte de `q-focus-helper`); el `outline` de `.tecla-viva` tampoco se veía: Quasar pone `.no-outline { outline: 0 !important }` en la capa `quasar_importants`. Hecho: la regla de foco va en `@layer base` con `!important`.
- [x] **[P2] Redibujo completo**: íconos escalados y fuentes en caché (`iconoEscalado`, `cargarFuente` en `dibujoBoton.py`) y vistas previas servidas por URL con hash (`/vista/{hash}`, caché `immutable`). Con las 46 teclas de `streamdeck.md`: redibujar el Deck pasó de ~400 a ~115 ms en el servidor y de ~553 a ~64 KB por websocket. Queda: el panel se reconstruye entero (~64 KB de DOM); `actualizarAcciones` → `mostrarPestañas()` solo lo llama `CargarAcciones`, que es código muerto.
- [ ] **[P2] `claseAccion()` en caliente**: `comandoAcción` y `mostrarOpciones` instancian todas las clases de acción en cada llamada; hacer un dict nombre → comando una vez.
- [x] **[P3]** Docstrings de atributos desplazados en `__init__`; `input`, `tipo` y `folder` sin usar en `actualizarPestaña`; ortografía "Interface" → "Interfaz" y `seDesconectoGUI` → `seDesconectaGUI`.
- [ ] **[P3]** Destello de la última acción con `rgba(94, 234, 212, 0.35)` fijo (duplica `--color-foco`).

## Ícono en la barra de estado (`bandeja.py`)

- [ ] **Último error en el menú**: en estado error, mostrar en la etiqueta la última línea de `journalctl --user -u elgarrobo -p err -n 1` para saber qué falló sin abrir la terminal.
- [ ] **Abrir carpeta de configuración**: opción del menú que abra `ObtenerFolderConfig()` con `xdg-open` para editar los `.md` a mano. La bandeja no importa elGarrobo, así que la ruta tendría que venir del ejecutable (ej. un subcomando) o por argumento en el `.desktop`.
- [ ] **Clic izquierdo abre la GUI**: con AppIndicator el clic izquierdo siempre abre el menú; `XApp.StatusIcon` lo permite pero solo existe en Mint/Cinnamon.
- [ ] **Reiniciar en modo depuración (`-d`)**: hoy el `ExecStart` del servicio es fijo; habría que pasarlo por una variable de entorno (`systemctl --user set-environment`) o un drop-in.
- [ ] **Logo propio**: reemplazar los íconos genéricos del tema (`input-keyboard` en el lanzador, `media-playback-*`/`dialog-error` por estado en `ESTADOS`).

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
- [x] **`ejecutar_elGarrobo.sh`**: llama a `elgarrobo-cli`, que ya no existe en `pyproject.toml`; lo reemplazan el menú y `elgarrobo servicio instalar`. Borrar.
- [ ] **`cargarDispositivos()` / `cargarModulos()`**: funciones que solo devuelven una lista literal; cambiar por constantes `DISPOSITIVOS = [...]` / `MODULOS = [...]`.

## Ortografía (requiere actualizar configs del usuario)

- [ ] Claves de macro `solisita` / `solisita_cambiar` → `solicita` / `solicita_cambiar` (ver CLAUDE.md).
- [ ] Métodos internos de `elGarrobo.py` (no requieren tocar configs): `SolisitarDibujar` → `SolicitarDibujar`, `SolisitarNotifiacacion` → `SolicitarNotificacion`.

## Configs del usuario (`~/dotfile/.config/elgarrobo/default/`)

- [ ] Imágenes que no existen: `freecad/geometria/linea.png`, `freecad/restricciones/distancia.png`, `inkscape/duplicar.png`.
- [x] `plus.md`: nombres "Uso Ran" → "Uso RAM" y "humedad Estudio" → "Humedad Estudio".
