# ElGatoALSW

Heramienta para aumentar la eficiencia y rapidez, en desarrollo y trabajo en produccion con diferentes heramientas, compatible con StreamDeck en Linux y multiples teclados

### Compatible con

-   El Gato StreamDeck
-   OBS_WebSoket
-   control MQTT
-   Linux y Python3

### Permite

-   Macros
-   delay
-   Ejecuccion de comando bash
-   Escribir texto
-   Folderes
-   Paginas
-   Abir folder proyecto

### Cosas por hacer

-   Gif
-   Sonidos
-   Reloc
-   Temperatura

### Instalar

```bash
pip3 install -r requiraments.txt
```

### Comando Ejecuccion

```bash
usage: ElGatoALSW [-h] [--master] [--cliente] [--deck] [--ratom] [--nodepurar] [--proyecto]

Heramienta de creacion de contenido de ALSW

optional arguments:
  -h, --help        show this help message and exit
  --master, -m      Cargar servidor de ElGatoALSW
  --cliente, -c     Cargando cliente de ElGatoALSW
  --deck, -d        Solo usar StreamDeck
  --ratom, -r       Solo usar Ratom Razer
  --nodepurar, -nd  Acivar modo sin depuracion
  --proyecto, -p    Configurar folder a proyecto actua
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

(comandos)[Comandos.md]
