## Atributos Basicos de cada Accion

| nombre          | tipo          | descripcion                                    | obligatorio | ejemplo     |
| --------------- | ------------- | ---------------------------------------------- | ----------- | ----------- |
| nombre          | string        | nombre para la depuracion                      | true        | MQTT        |
| titulo          | string        | Titulo para StreamDeck                         | false       | MQTT        |
| titulo_opciones | list          | Atributos extrar para titulo                   | false       |             |
| ket             | int or string | id para StreamDeck o nombre Tecla para Teclado | true        | 15 o KEY_Z  |
| imagen          | string        | direccion de la imagen o gif                   | false       | ./pollo.png |
| imagen_opciones | list          | Atributos extrar para imagen                   | false       |             |
| accion          | string        | accion a realizar, puede que necesite opciones | true        | reproducion |
| opciones        | list          | atributos extra para realizar la accion        | false       |             |


### Opciones extras para Titulos

Configuraciones extrar para el texto que aparece e la imagen o gif para el **StreamDeck**

**Ningunos** de los atributos extas son obligatorios

| nombre       | tipo    | descripcion                             | defecto | ejemplo |
| ------------ | ------- | --------------------------------------- | ------- | ------- |
| tamanno      | int     | Tamaño maximo del texto                 | 40      | 20      |
| ajustar      | boolean | Disminulle el tamaño que se lea cmpleto | true    | false   |
| alinear      | string  | Posicion texto (centro, ariba, abajo)   | abajo   | ariba   |
| color        | string  | Color en nombre ingles o hexa           | white   | #008080 |
| borde_color  | color   | color de borde de texto                 | black   | #ff0000 |
| borde_grosor | int     | tamaño del borde                        | 5       | 20      |


### Opciones Extrar para Imagenes 



| nombre | tipo | descripcion | defecto | ejemplo |
| ------ | ---- | ----------- | ------- | ------- |