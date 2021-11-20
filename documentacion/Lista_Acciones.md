# Acciones

## Accion Espera

Hace una pequeña espera entre acciones para macros.

```json
"accion": "delay"
```

**Opciones**

| nombre | tipo          | descripcion                                               | obligatorio | defecto | ejemplo  |
| ------ | ------------- | --------------------------------------------------------- | ----------- | ------- | -------- |
| tiempo | int or string | tiempo de espera en segundo int o formato 00:00:00 string | true        |         | 01:20:30 |

## Accion Mensaje MQTT

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

## Accion Accion OS

Ejecuta un comando de bash en linux

```json
"accion": "os"
```

**Opciones**

| nombre  | tipo   | descripcion          | obligatorio | defecto | ejemplo          |
| ------- | ------ | -------------------- | ----------- | ------- | ---------------- |
| comando | string | comando a ejecutarse | true        |         | mkdir SuperPollo |

## Accion Notificacion Escritorio 

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

## Accion Precionar combinacion de teclado

Presiona una combinacion de teclas para realizar una accion; se preciona en orde de izquierda a derecha y se sueltan invertido derecha a izquierda

Lista de Teclas disponibles (Link)

**Advertecia** primero debe ir teclas especiales como ctrl y shift

```json
"accion": "teclas"
```


| nombre | tipo | descripcion             | obligatorio | defecto | ejemplo                |
| ------ | ---- | ----------------------- | ----------- | ------- | ---------------------- |
| teclas | dict | combinaciones de teclas | true        |         | ["ctrl", "shift", "i"] |

## Accion Escribe un texto

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

## Accion Escribe un texto

Pegar texto con ctrl + v

```json
"accion": "pegar"
```

**Opciones**

| nombre    | tipo   | descripcion             | obligatorio | defecto | ejemplo    |
| --------- | ------ | ----------------------- | ----------- | ------- | ---------- |
| texto     | string | texto a ser escribir    | true        |         | Hola Mundo |
| intervalo | float  | tiempo entre cada texto | false       | 0.01    | 0.2        |

## Accion Copia texto 

Copia texto y lo devuelte al siquiente accion en una lista de macros

```json
"accion": "copiar"
```


**Opciones**

| nombre | tipo | descripcion | obligatorio | defecto | ejemplo |
| ------ | ---- | ----------- | ----------- | ------- | ------- |

**Devuelve**

String