# ElGatoALSW

Heramienta para aumentar la eficiencia y rapidez, en desarrollo y trabajo en produccion con diferentes heramientas, compatible con StreamDeck en Linux y multiples teclados

### Compatible con
* El Gato StreamDeck
* OBS_WebSoket
* control MQTT
* Linux y Python3

### Permite
* Macros
* Ejecuccion de comando bash
* Escribir texto
* Folderes
* Paginas

### Cosas por hacer
* Gif
* Sonidos
* Secuencias de Comandos
* Folder de trabajo

### Comando Ejecuccion

```bash
usage: ElGatoALSW.py [-h] [--master] [--cliente] [--deck] [--ratom] [--nodepurar]

Heramienta de creacion de contenido de ALSW

optional arguments:
  -h, --help        show this help message and exit
  --master, -m      Cargar servidor de ElGatoALSW.py
  --cliente, -c     Cargando cliente de ElGatoALSW.py
  --deck, -d        Solo usar StreamDeck
  --ratom, -r       Solo usar Ratom Razer
  --nodepurar, -nd  Acivar modo sin depuracion
```

# Carpetas listas

TODO: Agregar imagenes de otras Carpetas

### OBS

Control del editor de video

![Iconosl Blender](/Recursos/Blender/Pagina01.png)

# TODO

-   Instalador
-   Documentacion
-   Gif
-   Error fatal cuando se desconecta OBS

# Problemas

-   Precionar tecla Super

# Ejecuccion


```bash
python3 ElGatoALSW.py -h
  usage: ElGatoALSW.py [-h] [--master] [--cliente] [--deck] [--ratom]

  optional arguments:
    -h, --help     show this help message and exit
    --master, -m   Cargar servidor de ElGatoALSW.py
    --cliente, -c  Cargando cliente de ElGatoALSW.py
    --deck, -d     Solo usar StreamDeck
    --ratom, -r    Solo usar Ratom Razer

```

# Opciones de comando

Folder donde esta las descripcion de cada tecla de StreamDeck es **Botones.json** y las teclas que describen los teclados es **Teclado.json**

### Info Basica - Obligatorio
Informacion Minima de cada tecla

```json
{
  "Nombre": "---",
}
```

### Icono - Solo StreamDeck
Imagen con la que se activara la tecla, si no se define una una por defecto

```json
{
  "ico": "folder/imagen.png"
}
```

### Titulo Imagen - Solo StreamDeck
Titulo que aparecera debajo de la imagen, en ausencia se hara la imagen en maximo tamaño

```json
{
  "Titulo": "Titulo"
}
```

### Boton - solo teclado
Definicion de teclas de teclado, tambien se puede definir con mas opciones

```json
{
  "Boton": "KEY_1"
}
```

### Folder StreamDeck
Carga las teclas, que esten guardas dentro de un archivo **Botones.json**

```json
{
  "Cargar": "--/---/Botones.json",
  "Key": []
}
```

### Folder Teclado
Carga las configuraciones, que dentro de un folder, el **Raton_Razere** es considerado un teclado

```json
{
  "CargandoRaton": "--/---/Teclado.json",
  "teclado": []
}
```

### Acciones teclado
Preciona la tecla en la pc master, puede ser de una tecla o multiples

```json
{
  "tecla": ["ctrl", "alt", "t"]
}
```

### Comando Sistema Operativo
Ejecutca un comando en bash en pc master

```json
{
  "OS": "nemo $HOME/2.VideoMusicales"
}
```

### Escribir texto
Escribe un texto automaticamente con sierta velocidad

```json
{
  "texto": "https://www.youtube.com/alswnet"
}
```

### Regresar dentro folder
Regresa al inicio de la aplicacion

```json
{
  "Regresar": "True"
}
```

### Siquiente pantalla
Mueve las seleciones a la siquiente pantalla de haberlo

```json
{
  "Siquiente": true
}
```

### Anterior pantalla
Mueve las seleciones a la anterior pantalla de haberlo

```json
{
  "Anterior": true
}
```

# Comandos OBS
Contro y manejo de OBS Estudio por medio del plugin OBS_WebSoket. Los botones no funcionaran si no se hay coneccion con OBS

### Conectar OBS
Para conectarse a OBS el programa debe estar encendido y el plugin de OBS_WebSoket activado, dentro de la misma red, el nombre de la pc se una para conectarse

```json
{
  "OBS": "ryuk.local"
}
```

### Empezar/Parar grabacion
Empieza o para la grabacion, cambia de icono si esta definido dependiendo del estado de OBS

```json
{
  "Grabar": true,
  "Estado": false,
  "icon_true": "Recursos/OBS/RecOn.png",
  "icon_false": "Recursos/OBS/RecOff.png"
}
```

### Empezar/Parar trasmicion en vivo
Empieza o para la trasmicion en vivo, cambia de icono si esta definido dependiendo del estado de OBS

```json
{
  "Live": true,
  "Estado": false,
  "icon_true": "Recursos/OBS/LiveOn.png",
  "icon_false": "Recursos/OBS/LiveOff.png"
}
```

### Cambia Esena
Cambia Esena y muestra imagen diferente si la esena esta activa dependiendo del estado de OBS

```json
{
  "CambiarEsena": "Codigo",
  "Estado": false,
  "icon_true": "Recursos/OBS/CodigoOn.png",
  "icon_false": "Recursos/OBS/CodigoOff.png"
}
```

### Cambia Estado de Fuente
Cambian el estado de visibilidad de una fuente y cambia la imagen en base al estado de OBS

```json
{
  "Fuente": "Camara",
  "Estado": true,
  "icon_true": "Recursos/OBS/CamaraOn.png",
  "icon_false": "Recursos/OBS/CamaraOff.png"
}
```

### Cambia Estado de Filtro de Fuente
Cambian el estado de visibilidad de un filtro de una fuente y cambia la imagen en base al estado de OBS

```json
{
  "Fuente": "Camara",
  "Filtro": "Verde",
  "Estado": true,
  "icon_true": "Recursos/OBS/VerdeOn.png",
  "icon_false": "Recursos/OBS/VerdeOff.png"
}
```

## Comandos MQTT - Computadora Remota
Mandar senales por medio de red a una pc dentro de la red por MQTT

### Acciones teclas - Computadora Remota
Preciona la tecla en la pc cliente, puede ser de una tecla o multiples

```json
{
  "mqtt": "Key ctrl alt t"
}
```

### Comando Sistema Operativo - Computadora Remota
Preciona la tecla en la pc cliente, puede ser de una tecla o multiples

```json
{
  "mqtt": "nemo $HOME/2.VideoMusicales"
}
```

# Proyecto Activo
Abre el folder del proyecto activo mas parametro

```json
{
    "Proyecto": "1.Guion"
}
```


### Lista de Teclas disponibles
Lista de teclas disponibles

```json
{
  '\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',
  ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
  '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
  'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
  'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
  'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
  'browserback', 'browserfavorites', 'browserforward', 'browserhome',
  'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
  'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
  'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
  'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
  'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
  'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
  'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
  'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
  'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
  'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
  'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
  'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
  'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
  'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
  'command', 'option', 'optionleft', 'optionright'
}
```
