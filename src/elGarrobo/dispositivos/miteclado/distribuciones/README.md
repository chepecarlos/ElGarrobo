# Distribuciones de teclado

Una distribución dibuja tu teclado en la GUI con su forma real, en vez de verlo como una lista de acciones. Sirve
para teclados USB, macropads y ratones que se conectan como teclado (ej. Razer Naga).

En la vista del teclado:

- **Click en una tecla con acción** (verde): la abre en el editor.
- **Click en una tecla vacía** (gris): prepara una acción nueva con ese keycode.
- **Intercambiar**: mueve acciones entre teclas.
- **Otras teclas**: acciones en teclas que no están dibujadas (ej. capa Fn) aparecen abajo para que no queden escondidas.

Pasa el mouse sobre una tecla para ver su keycode.

## Elegir una distribución

En la pestaña del teclado presiona **Distribución**. Sale la lista de las disponibles con una miniatura; al elegir
una se guarda en `teclados.md`. **Ninguna** vuelve a la vista de lista.

También se puede escribir a mano en `~/.config/elgarrobo/teclados.md`:

```yaml
---
- nombre: Teclado Normal
  dispositivo: /dev/input/by-id/usb-DREVO.Inc_BladeMaster_TE_87K-event-kbd
  archivo: drevo
  distribucion: ingles_87k
---
```

## Incluidas

| Nombre | Teclado |
|---|---|
| `ingles_104` | Completo en inglés (ANSI) con teclado numérico |
| `ingles_87k` | Sin teclado numérico (TKL), inglés |
| `espannol_87k` | Sin teclado numérico (TKL), español (ISO, con Ñ y `<`) |
| `ingles_60` | 60%, sin fila de F ni flechas |
| `numpad_17` | Solo teclado numérico |
| `sonix_una_mano` | Medio teclado gamer de una mano (G1–G6 = F1–F6) |
| `razer_naga_2` / `_6` / `_12` | Placas laterales del Razer Naga Pro |

## Agregar una propia

Pon un `.json` en `~/.config/elgarrobo/distribuciones/` (crea la carpeta si no existe). El nombre del archivo es
el nombre en la lista y no hace falta reiniciar. Si se llama igual que una incluida, se usa la tuya.

Hay dos formatos y ElGarrobo detecta cuál es.

### Desde keyboard-layout-editor.com (recomendado)

1. Dibuja el teclado en [keyboard-layout-editor.com](https://www.keyboard-layout-editor.com). Puedes empezar
   desde **Presets**.
2. **Download → Download JSON**.
3. Copia el archivo a la carpeta.

El keycode de cada tecla sale de su leyenda:

| Leyenda | Keycode |
|---|---|
| `KEY_F13` | `KEY_F13`, se usa tal cual |
| `KEY_F13` y `G1` en otra línea | `KEY_F13`, mostrando "G1" |
| `Q`, `F1`, `Tab`, `Esc`, `Enter`, `Home` | `KEY_` + leyenda |
| `Shift`, `Ctrl`, `Alt`, `Win` | la primera es la izquierda, la segunda la derecha |
| `←` `↑` `→` `↓`, `PgUp`, `Del`, `` ` ``, `[`, `;`… | alias comunes |
| vacía | `KEY_SPACE` (la primera) |

Las teclas cuyo keycode no se reconoce se omiten. Pasa con teclas que repiten un keycode ya usado: en el numpad
`7 Home` choca con `KEY_7` y `KEY_HOME` del teclado principal; ponle `KEY_KP7` como leyenda. La rotación de
teclas de KLE se ignora.

### Formato ElGarrobo

Una lista con una tecla por línea. `x`, `y`, `w` (ancho) y `h` (alto) van en unidades de tecla, `w` y `h` valen
1 si no se ponen. `etiqueta` es el texto que se muestra; sin ella se muestra el keycode sin `KEY_`.

```json
[
  {"key": "KEY_ESC", "x": 0, "y": 0},
  {"key": "KEY_TAB", "x": 0, "y": 1, "w": 1.5},
  {"key": "KEY_KPENTER", "x": 3, "y": 3, "h": 2, "etiqueta": "Enter"}
]
```

## ¿Qué keycode manda mi tecla?

Corre `elgarrobo -d` y presiona la tecla: el log muestra `NombreTeclado[KEY_...-PRESIONADA]`. También sirve
`sudo evtest`. Teclas como **Fn** no mandan nada y no se pueden usar.

La distribución solo cambia el dibujo: el keycode es el mismo aunque las letras impresas sean de otro idioma.
