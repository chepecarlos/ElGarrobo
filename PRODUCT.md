# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Público general en Linux: cualquier persona con un StreamDeck, teclados USB extra (incluido el Razer Naga), un pedal o controles MQTT que quiera usarlos como macros. No se asume que sepa editar archivos `.md`/`.json`; la GUI tiene que dejarle configurar y usar todo sin abrir un editor de texto.

## Product Purpose

ElGarrobo convierte teclas físicas y virtuales en acciones: atajos, escribir texto, sonidos, control de OBS, mensajes MQTT, cambio de folders/páginas y macros encadenadas. Busca hacer más rápido y eficiente el trabajo diario y la producción (por ejemplo, streaming y grabación).

La GUI web (`elgarrobo -g`, hecha con NiceGUI) cumple tres funciones:
- **Editor de configuración**: acciones, apariencia de botones, módulos y dispositivos.
- **Botonera virtual**: presionar botones y macros desde el navegador.
- **Visualización de teclados**: ver cómo están mapeados los teclados USB, el Razer Naga y el StreamDeck.

Tiene éxito cuando alguien conecta sus dispositivos y deja macros funcionando desde la GUI, sin tocar archivos a mano.

## Positioning

- **Muchos dispositivos en un solo sistema**: StreamDeck (también combinados como "deck combinado"), teclados USB, pedal y MQTT comparten las mismas acciones, perfiles y folders.
- **Macros encadenadas**: las acciones se ejecutan en secuencia y el "cajón" pasa datos de un paso al siguiente (`macro_opciones`).

## Operating Context

- Escritorio Linux, normalmente durante un stream, una grabación o trabajo con herramientas como OBS, FreeCAD, Inkscape u Octoprint.
- La configuración se guarda en archivos `.md` con frontmatter YAML o `.json`, por perfil, dentro de `ObtenerFolderConfig()/<perfil>/`. `modulos.md` habilita los dispositivos y módulos.
- Navegación jerárquica por folders y páginas, en el dispositivo y en la GUI.

## Capabilities and Constraints

- La GUI es NiceGUI (Python). Las páginas actuales son `/`, `/modulos` y `/dispositivos`, en `src/elGarrobo/dispositivos/migui/migui.py`.
- La GUI lee y escribe los mismos archivos de configuración del usuario. Las claves persistidas (`comando` de cada acción y claves de `opciones`/`macro_opciones`) no pueden cambiar sin migrar las configs, porque se rompen macros ya guardadas.
- Las propiedades de cada acción salen de `listaPropiedades` (`propiedadAccion`: tipo, obligatoria y `multilinea`). Los formularios del editor se generan a partir de ellas.
- La interfaz y la documentación están en español.
- Pendiente: editar los pasos de las macros en la GUI (hoy se muestran en YAML de solo lectura).
- Pendiente: la pantalla táctil y las perillas del StreamDeck Plus en la GUI.
- Pendiente: más campos de apariencia en el editor (imagen, color del título, rotación, tamaño de fuente).
- Pendiente: la vista previa con deck combinado usa siempre el primer StreamDeck (ver `mejoras.md`).

## Evidence on Hand

- `README.md`, `Guia_Instalacion.md`, `Comandos.md`, `mejoras.md` y `demo/`.
- Distribuciones de teclado en `src/elGarrobo/dispositivos/miteclado/distribuciones/`.
- No hay testimonios, métricas de uso ni casos de estudio; no inventarlos.

## Product Principles

1. **Configurable sin editar archivos**: todo lo que se puede hacer en un `.md` debería poder hacerse desde la GUI, para un usuario que no es programador.
2. **Los archivos del usuario son sagrados**: la GUI guarda en el mismo formato y nunca rompe claves ni macros existentes.
3. **Un solo modelo para todos los dispositivos**: lo que se aprende en un dispositivo vale en los demás (acciones, folders, perfiles).
4. **Rapidez en uso real**: presionar un botón, ver el resultado y seguir trabajando, a menudo en vivo.
