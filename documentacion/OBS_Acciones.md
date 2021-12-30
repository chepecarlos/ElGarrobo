# Lista de Accione OBS WebSockets

Necesario instalar y condigurar plugin extra para OBS - [OBS WebSockets](https://obsproject.com/forum/resources/obs-websocket-remote-control-obs-studio-from-websockets.466/)

## 1 Accion Conectar a OBS

Conectar a OBS WebSockets

```json
"accion": "obs_conectar"
```

**Opciones:**

| nombre      | tipo   | descripcion                         | obligatorio | defecto   | ejemplo       |
| ----------- | ------ | ----------------------------------- | ----------- | --------- | ------------- |
| host        | string | ip o direcion mdns de la pc con obs | false       | localhost | 192.168.50.69 |
| puerto      | int    | puerto de coneccion                 | false       | 4444      | 1234          |
| contrasenna | string | contraseña de obs web Soket         | false       | null      | SubALSW       |

## 2 Desconectar

Desconectar de OBS WebSockets

```json
"accion": "obs_desconectar"
```

**Opciones:**

| nombre | tipo | descripcion | obligatorio | defecto | ejemplo |
| ------ | ---- | ----------- | ----------- | ------- | ------- |

## 3 Cambiar estado Grabacion

Cambiar el estado de grabacion de OBS

```json
"accion": "obs_grabar"
```

**Opciones:**

| nombre | tipo | descripcion | obligatorio | defecto | ejemplo |
| ------ | ---- | ----------- | ----------- | ------- | ------- |

## 4 Cambiar estado Transmision

Cambiar el estado de transmicion de OBS

```json
"accion": "obs_envivo"
```

**Opciones:**

| nombre | tipo | descripcion | obligatorio | defecto | ejemplo |
| ------ | ---- | ----------- | ----------- | ------- | ------- |

## 5 Cambiar estado Camara Virtual

Cambia el estado de Camara Virtual

```json
"accion": "obs_camara_virtual"
```

## 6 Cambia Esena

Cambia esena a actual

```json
"accion": "obs_escena"

```

**Opciones:**

| nombre | tipo   | descripcion        | obligatorio | defecto | ejemplo        |
| ------ | ------ | ------------------ | ----------- | ------- | -------------- |
| escena | String | Nombre de la esena | true        |         | Esena_principa |

## 7 Cambiana Fuente

Activa de Visiable a No Visible una fuente

```json
"accion": "obs_fuente"
```

**Opciones:**

| nombre | tipo   | descripcion         | obligatorio | defecto | ejemplo |
| ------ | ------ | ------------------- | ----------- | ------- | ------- |
| fuente | string | nombre de la fuente | true        |         | camara  |

## 8 Cambiar Filtro Fuente

```json
"accion": "obs_filtro"
```

**Opciones:**

| nombre | tipo   | descripcion       | obligatorio | defecto | ejemplo     |
| ------ | ------ | ----------------- | ----------- | ------- | ----------- |
| filtro | string | nombre del filtro | true        |         | fondo_verde |
| fuente | string | npmbre del fuente | true        |         | camara      |
