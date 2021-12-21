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

