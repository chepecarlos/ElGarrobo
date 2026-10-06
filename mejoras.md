# Mejoras pendientes

## Dibujo de botones

- [ ] **Títulos que no caben con imagen**: desde que `calcularTamañoFuente` respeta el mínimo, con imagen el título no baja de 20 y los largos se cortan ("equence", "ondoOB"). Opciones:
  - (a) aplicar el mínimo de 20 solo si el texto cabe; si no, achicar como antes.
  - (b) quitar el mínimo automático con imagen y dejar solo `titulo_opciones.tamanno_minimo`.
- [ ] **Editor de apariencia**: agregar más campos además de título y fondo: `imagen`, color del título, rotar, tamaño de fuente (`titulo_opciones`).
- [ ] **Vista previa en el editor con deck combinado**: usa siempre el primer StreamDeck (tamaño y rotación); debería usar el StreamDeck al que pertenece la tecla.

## Deck combinado / StreamDeck

- [ ] **Numeración estable**: `baseTeclas` se calcula al conectar con los botones de los StreamDeck conectados. Si uno está desconectado, el otro empieza en 1 y ejecuta acciones ajenas (y la cuadrícula de la GUI se solapa). Reservar siempre los botones de cada StreamDeck (ej. 15).
- [ ] **Layout sin conectar**: un StreamDeck desconectado se asume 3x5; podría guardarse el layout en `deck_combinado.md`.
- [ ] **StreamDeck Plus en la GUI**: la cuadrícula muestra las 8 teclas, falta la pantalla táctil y las perillas.

## GUI

- [ ] **Editar pasos de macros**: hoy se muestran en YAML de solo lectura y se conservan al guardar; solo se editan en el `.md`.

## Código

- [ ] **Interfaz tipo dict de `dataAccion`** (`get`, `[]`, `in`, `items`): quitarla cuando los dispositivos usen los campos directamente (marcada con `ponytail:` en `dataAccion.py`).
- [ ] **`folderActual` inicial `"/"`**: con ese valor, cargar un folder relativo antes que la raíz se rechaza ("fuera de folder perfil"); en la app no pasa porque siempre se carga la raíz primero.
- [ ] **`EnviarMensajeMQTT`** (miLibrerias): `accionMQTT` ya no la usa (reusa conexiones); revisar si queda algún uso o se puede quitar.

## Ortografía (requiere actualizar configs del usuario)

- [ ] Comando `siquiente_pagina` → `siguiente_pagina` (clave en `cargarClasesAcciones()`, también `imagen_base.siquiente_pagina` y `base/siquiente.png` en los configs).
- [ ] Claves de macro `solisita` / `solisita_cambiar` → `solicita` / `solicita_cambiar` (ver CLAUDE.md).

## Configs del usuario (`~/dotfile/.config/elgarrobo/default/`)

- [ ] `octoprint/streamdeck.md`: error de sintaxis YAML en la línea 107, no se carga.
- [ ] Imágenes que no existen: `freecad/geometria/linea.png`, `freecad/restricciones/distancia.png`, `inkscape/duplicar.png`.
