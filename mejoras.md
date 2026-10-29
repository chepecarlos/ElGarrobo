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
- [x] **Temas claro y oscuro**: selector Automático/Claro/Oscuro en /configurar, guardado en `gui_preferencias` (`tema`: `auto`, `claro`, `oscuro`; por defecto `oscuro`) y aplicado con `ui.dark_mode()` en cada página. Acento, foco y errores son variables CSS en `tema.py` que cambian con `body--dark` (claro: teal-700 5.5:1, red-700 6.5:1); la cabecera y la carcasa quedan oscuras en los dos temas. En la cabecera y no en /configurar habría quedado muy llena.
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

### Crítica de /dispositivos (2026-10-21, `/impeccable critique`: 22/40)

- [x] **[P1] Estado de reinicio invisible**: el switch se aplica al reiniciar, Agregar/Quitar al momento y el orden al volver a Acciones; el aviso se iba con el toast. Hecho: `miGui.pendientesReinicio` (`marcarPendiente()` en `configuracion.py`), botón ámbar "Reiniciar para aplicar" en la cabecera de todas las páginas con tooltip de lo pendiente, etiqueta "Pendiente de reinicio" junto al tipo cambiado (se quita si el switch vuelve a como estaba) y aviso que dice qué se aplica al momento y qué al reiniciar.
- [x] **[P0] La GUI se podía apagar a sí misma**: un toque dejaba al usuario sin GUI tras reiniciar y `elgarrobo -g` no la forzaba (pasaba `gui="true"` que nadie leía). Hecho: /dispositivos ya no lista "Interfaz Gráfica" y `-g` la enciende en memoria aunque esté apagada en `dispositivos.md` (`iniciarModulo`); también queda `elgarrobo dispositivos activar gui`.
- [x] **[P2] El reinicio se veía peligroso y no decía qué estaba pendiente**: el diálogo iba en rojo como Salir y la lista solo estaba en el tooltip del botón (no se ve en celular ni con teclado); editar un aparato no marcaba ninguna fila. Hecho: `crearDialogoReiniciar` lista los cambios pendientes y confirma con "Reiniciar ahora" en ámbar (en el color de los botones si no hay pendientes); la etiqueta "Pendiente de reinicio" del tipo también se enciende por sus aparatos u opciones editados.
- [ ] **[P3] Apagar un tipo con aparatos sin aviso**: apagar Teclado Macro con teclados agregados no pregunta; se puede volver a encender desde la GUI, por eso es menor. Si molesta, `dialogoPregunta` en `cambiarEstado`.
- [x] **[P1] Estados vacíos sin salida**: "No hay aparatos en pedal.md" mandaba a editar un archivo sin decir dónde. Hecho: ícono del tipo + "Aún no hay ningún …" + cómo agregarlo ("Conecta uno y presiona Agregar teclado", o la ruta completa `~/.config/elgarrobo/<archivo>` si todavía no hay asistente); con el tipo apagado se lee "Activa Teclado Macro para agregar uno" junto al botón en vez del tooltip del botón deshabilitado; al agregar, el aviso dice dónde asignar sus teclas.
- [x] **[P1] Agrupación rota**: el `border-b` estaba en la fila del switch, así que los aparatos y el estado vacío caían debajo del divisor y se leían como parte del tipo siguiente. Hecho (también en /modulos): una sección por tipo con el divisor al final, nombre del tipo como encabezado nivel 3 y más grande, aparatos y opciones como filas sin borde (`expand-separator`) alineadas con el nombre (`CONTENIDO_TIPO`, menos sangría en celular), ancho `max-w-3xl` y el aviso en texto normal en vez de caption.
- [x] **[P2] Estado de cada aparato**: no se sabía si un teclado o StreamDeck estaba conectado sin ir a Acciones a probarlo. Hecho: chip con punto y texto junto al caption (`estadoAparato()`), se actualiza cada 2 s: Conectado, Desconectado, "1 de 2 conectados" en grupos de StreamDeck, "Se carga al reiniciar" (agregado a mano o tipo recién activado) y Apagado (tipo apagado y sin cargar).
- [ ] **[P2] Atenuar los aparatos de un tipo apagado**: siguen viéndose activos y con Guardar/Quitar (el chip ya dice Apagado).
- [ ] **[P1] Agregar pedal, StreamDeck y MQTT desde la GUI**: solo los teclados tienen asistente (`listarDisponibles`); los demás se agregan a mano en su `.md`. El pedal y el StreamDeck se podrían detectar con `DeviceManager().enumerate()` (número de serie) y MQTT es un formulario (broker, usuario, contraseña, tópico de control).
- [x] **[P2] "Ordenar pestañas" en /dispositivos**: era el botón más pesado de la página, perdía el foco al mover y mostraba el tipo crudo (`deck_combinado`). Hecho: botón de la barra de herramientas en Acciones (solo Editar y con más de un dispositivo), las pestañas se mueven en vivo, el foco vuelve al botón, `aria-live` con la posición y nombre de la clase en vez del tipo.
- [ ] **[P2] Diálogo Agregar teclado**: Guardar queda cortado al pie (scroll `max-h-80` anidado dentro del del diálogo, `agregar.py:121`); distribuciones y teclas crudas (`ingles_87k`, `KEY_ENTER`). Navegación del stepper fija al pie, un solo scroll, nombres legibles ("Inglés 87 teclas (TKL)", "Enter") con el código en tooltip.
- [ ] **[P2] Contraste del stepper**: paso activo `#00786f` sobre `#1d1d1d` da 3.1:1 en oscuro (`primary` como texto); el inactivo `#9e9e9e` sobre blanco da 2.7:1 en claro.
- [ ] **[P3] Celular**: con el StreamDeck Plus la barra de herramientas pasa a 3 filas por el botón de ordenar; si estorba, `max-sm:hidden`.
- [ ] **[P3]** `bind_enabled_from` habilita Agregar al activar el tipo aunque no carga hasta reiniciar (contradice el comentario de `configuracion.py`); ícono de lápiz de Quasar en el paso "Buscar"; `colorActivo` (naranja) en la tarjeta elegida significa "herramienta encendida" en Acciones; sin `truncate` en expansiones con nombres largos.
- [ ] **[P3] Diagnóstico de permisos**: un teclado sin permiso de `/dev/input` sale como "(desconectado)" y `escucharTeclado` se traga el `OSError` (`agregar.py:24-27`); decir "sin permiso: agrega tu usuario al grupo input".
- [ ] **[P3] Copy**: "aparato" vs "dispositivo" sin explicar; "Interfaz web/gráfica (GUI)" redundante; "macro pad" → "panel de macros"; nombres camelCase visibles en /modulos (`estadoPc`, `estadoKlipper`).

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
