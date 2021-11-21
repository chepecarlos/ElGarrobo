# Acciones

## 1 Accion Espera

Hace una pequeña espera entre acciones para macros.

```json
"accion": "delay"
```

**Opciones**

| nombre | tipo          | descripcion                                               | obligatorio | defecto | ejemplo  |
| ------ | ------------- | --------------------------------------------------------- | ----------- | ------- | -------- |
| tiempo | int or string | tiempo de espera en segundo int o formato 00:00:00 string | true        |         | 01:20:30 |

## 2 Accion Mensaje MQTT

Envia mensaje por mqtt

```json
"accion": "mqtt"
```

**Opciones**

| nombre      | tipo   | descripcion                   | obligatorio | defecto                      | ejemplo                   |
| ----------- | ------ | ----------------------------- | ----------- | ---------------------------- | ------------------------- |
| mensaje     | string | mensaje a ser enviado         | true        |                              | "hola mundo"              |
| opciones    | list   | Mensar por lista de atributos | false       |                              | {"nombre": "chepecarlos"} |
| topic       | string | tema a publicar video         | true        |                              | alsw/temperatura          |
| usuario     | string | Usuario del broker MQTT       | false       | usuario>"data/mqtt.json"     | ChepeCarlos               |
| contrasenna | string | contraseña del broker MQTT    | false       | contrasenna>"data/mqtt.json" | ALSW                      |
| servidor    | string | Broker MQTT                   | false       | servidor>"data/mqtt.json"    | test.mosquitto.org        |
| puerto      | string | puerto del broker             | false       | puerto>"data/mqtt.json"      | 1883                      |

## 3 Accion Accion OS

Ejecuta un comando de bash en linux

```json
"accion": "os"
```

**Opciones**

| nombre  | tipo   | descripcion          | obligatorio | defecto | ejemplo          |
| ------- | ------ | -------------------- | ----------- | ------- | ---------------- |
| comando | string | comando a ejecutarse | true        |         | mkdir SuperPollo |

## 4 Accion Notificacion Escritorio

Muestra una Notifacion de Escritorio

```json
"accion": "notificacion"
```

**Opciones**

| nombre         | tipo    | descripcion                             | obligatorio | defecto    | ejemplo            |
| -------------- | ------- | --------------------------------------- | ----------- | ---------- | ------------------ |
| texto          | string  | mensaje a mostar                        | true        |            | Hola mundo         |
| titulo         | string  | titulo del mensaje                      | false       | ElGatoALSW | Mirame             |
| icono          | String  | direccion del icono                     | false       |            | /folder/imagen.png |
| icono_relativo | boolean | icono direccion es relativa al proyecto | false       | false      | true               |

## 5 Accion Precionar combinacion de teclado

Presiona una combinacion de teclas para realizar una accion; se preciona en orde de izquierda a derecha y se sueltan invertido derecha a izquierda

Lista de Teclas disponibles (Link)

**Advertecia** primero debe ir teclas especiales como ctrl y shift

```json
"accion": "teclas"
```

| nombre | tipo | descripcion             | obligatorio | defecto | ejemplo                |
| ------ | ---- | ----------------------- | ----------- | ------- | ---------------------- |
| teclas | dict | combinaciones de teclas | true        |         | ["ctrl", "shift", "i"] |

## 6 Accion Escribe un texto

Escribe un texto con un retrardo entre cada carracter

Lista de Teclas disponibles (Link)

```json
"accion": "escribir"
```

**Opciones**

| nombre    | tipo   | descripcion             | obligatorio | defecto | ejemplo    |
| --------- | ------ | ----------------------- | ----------- | ------- | ---------- |
| texto     | string | texto a ser escribir    | true        |         | Hola Mundo |
| intervalo | float  | tiempo entre cada texto | false       | 0.01    | 0.2        |

## 7 Accion Escribe un texto

Pegar texto con ctrl + v

```json
"accion": "pegar"
```

**Opciones**

| nombre    | tipo   | descripcion             | obligatorio | defecto | ejemplo    |
| --------- | ------ | ----------------------- | ----------- | ------- | ---------- |
| texto     | string | texto a ser escribir    | true        |         | Hola Mundo |
| intervalo | float  | tiempo entre cada texto | false       | 0.01    | 0.2        |

## 8 Accion Copia texto

Copia texto y lo devuelte al siquiente accion en una lista de macros

```json
"accion": "copiar"
```

**Opciones**

| nombre | tipo | descripcion | obligatorio | defecto | ejemplo |
| ------ | ---- | ----------- | ----------- | ------- | ------- |

**Devuelve**

String

## 9 Accion Repoduccion

Agrega la repoduccion de sonido a la lista

Formatos: wav

```json
"accion": "reproducion"
```

**Opciones**

| nombre   | tipo   | descripcion                        | obligatorio | defecto             | ejemplo           |
| -------- | ------ | ---------------------------------- | ----------- | ------------------- | ----------------- |
| sonido   | string | sonido a reproducir en formaro waw | true        |                     | golpe.mp3         |
| ganancia | int    | decinevel mas o menos              | false       | 0                   | -5                |
| folder   | string | ruta del sonido                    | false       | dolder del proyecto | /home/chepecarlos |

## 10 Parar todas las repdocucciones

Para todas los sonidos en la lista que esten activos

```json
"accion": "detener_reproducion"
```

**Opciones**

| nombre | tipo | descripcion | obligatorio | defecto | ejemplo |
| ------ | ---- | ----------- | ----------- | ------- | ------- |

## 11 Leer archivo

Lee un archivo y devuelve devuelve valor a siquiente macro

```json
"accion": "leer_valor"
```

**Opciones**

| nombre   | tipo   | descripcion                | obligatorio | defecto | ejemplo       |
| -------- | ------ | -------------------------- | ----------- | ------- | ------------- |
| archivo  | string | archivo a abir             | true        |         | data/obs.json |
| atributo | string | si existe saca del archivo | false       |         | camara        |

**Devuelve**

String | int | boolean | list

## 12 Escribir archivo

Escribe informacion en un archivo

```json
"accion": "escrivir_valor"
```

**Opciones**

| nombre   | tipo                             | descripcion                           | obligatorio | defecto | ejemplo       |
| -------- | -------------------------------- | ------------------------------------- | ----------- | ------- | ------------- |
| archivo  | string                           | ruta del archivo                      | true        |         | data/obs.json |
| atributo | string                           | si existe agrega el valor en atributo | false       |         | camara        |
| valor    | int or string or list or boolean | dato a guardar                        | true        |         | pollo         |
| local    | boolean                          | esta dentro de config el archivo      | false       | true    | false         |

## 13 Cerrar ventana

Activa cursos para cerrar ventana

```json
"accion": "cerrar_ventana"
```

**Opciones**

| nombre | tipo | descripcion | obligatorio | defecto | ejemplo |
| ------ | ---- | ----------- | ----------- | ------- | ------- |

## 14 Buscar ventana

Busca una ventana en base al nombre de la ventana

```json
"accion": "mostar_ventana"
```

**Opciones**

| nombre | tipo   | descripcion                 | obligatorio | defecto | ejemplo |
| ------ | ------ | --------------------------- | ----------- | ------- | ------- |
| nombre | string | nombre de la venta a buscar | true        |         | obs     |
