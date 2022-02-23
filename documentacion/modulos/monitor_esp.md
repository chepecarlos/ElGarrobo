# Monitor ESP's 

Modulo de Monitore por MQTT para ESP's para poder mostar informacion de ElGatoALSW

Informacion disponible:
* accion
  * tipo
  * nombre
  * key
  * dispositivo (pendiente)
* folder
  * folder
  * directorio
  * pagina (pendiente)
* obs (pendiente)
  * conectado
  * grabando
  * transmitiendo
  * virtual_camara
  * esena
* pulse (pendiente)
  * dispositivo 
  * nivel

## Configuracion

Debe ser activado en archivo **modulo.json** por defecto esta apagado

| nombre      | tipo    | descripcion                       | defecto | ejemplo |
| ----------- | ------- | --------------------------------- | ------- | ------- |
| monitor_esp | boolean | Monitor MQTT para ESP del sistema | false   | true    |

Para configurar el modulo debe ser crear archivo **mqtt.json** dentro de folder modulos con el nombre **monidor_esp**

| nombre                 | tipo   | descripcion                  | defecto          | ejemplo            |
| ---------------------- | ------ | ---------------------------- | ---------------- | ------------------ |
| topic                  | string | topic base a publicar estado |                  | "alsw/monitor_esp" |
| server (pendiente)     |        |                              | mqtt.json Global |                    |
| puerto (pendiente)     |        |                              | mqtt.json Global |                    |
| usuario (pendiente)    |        |                              | mqtt.json Global |                    |
| contraseña (pendiente) |        |                              | mqtt.json Global |                    |


# Monitor de OBS

Mensajes que enviar por MQTT cuando una evento con obs

| Estado            | Descripción                                                              |
| ----------------- | ------------------------------------------------------------------------ |
| OBS-Conectado     | Ya puede controlar OBS                                                   |
| OBS-No-Encontrado | No se puedo conectar a OBS, tal vez no abierto o no activo OBS Websocket |
| OBS-No-Conectado  | OBS se a desconectado la conexión                                        |
| OBS-Ya-Conectado  | No necesario re-conectar ya esta conectado                               |
| OBS-Grabando      | Empezando a grabar                                                       |
| OBS-No-Grabado    | Terminando de grabar                                                     |
| OBS-EnVivo        | Empezar el streaming                                                     |
| OBS-No-EnVivo     | Terminando el streaming                                                  |
