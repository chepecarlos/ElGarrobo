var OBSWebSocket = require('obs-websocket-js');

console.log(process.argv[2]);

const obs = new OBSWebSocket();
obs.connect({
  address: 'ryuk.local:4444'
}).then(() => {
  console.log(`Conectado CambiadorOBS`);
  if (process.argv[2] == "Esena") {
    console.log("Cambiar Esena")
    obs.send('SetCurrentScene', {
      'scene-name': process.argv[3]
    });
  } else if (process.argv[2] == "Striming") {
    console.log("Cambiar Estado Striming")
    if (process.argv[3] == "Activar") {
      obs.sendCallback('StartStreaming', (error) => {
        if (error) {
          console.log(error);
        }
      });
    } else if (process.argv[3] == "Desactivar") {
      obs.sendCallback('StopStreaming', (error) => {
        if (error) {
          console.log(error);
        }
      });
    }
  } else if (process.argv[2] == "Grabar") {
    console.log("Cambiar Estado Grabacion")
    if (process.argv[3] == "Activar") {
      obs.sendCallback('StartRecording', (error) => {
        if (error) {
          console.log(error);
        }
      });
    } else if (process.argv[3] == "Desactivar") {
      obs.sendCallback('StopRecording', (error) => {
        if (error) {
          console.log(error);
        }
      });
    }
  } else if (process.argv[2] == "Mute") {
    console.log("Cambiando mute");
    if (process.argv[3] == "Activar") {
      obs.sendCallback('SetMute', {
        'source': process.argv[4],
        'mute': false
      }, (error, data) => {
        if (error) {
          console.log(error);
        }
        console.log(data)
      });
    } else if (process.argv[3] == "Desactivar") {
      obs.sendCallback('SetMute', {
        'source': process.argv[4],
        'mute': true
      }, (error, data) => {
        if (error) {
          console.log(error);
        }
        console.log(data)
      });
    }
  } else if (process.argv[2] == "Filtro") {
    console.log("Cambiar pantalla Filtro ??");
    if (process.argv[3] == "Activar") {
      obs.sendCallback('SetSourceFilterVisibility', {
        'sourceName': process.argv[4],
        'filterName': process.argv[5],
        'filterEnabled': true
      }, (error, data) => {
        if (error) {
          console.log(error);
        }
        console.log(data)
      });
    } else if (process.argv[3] == "Desactivar") {
      obs.sendCallback('SetSourceFilterVisibility', {
        'sourceName': process.argv[4],
        'filterName': process.argv[5],
        'filterEnabled': false
      }, (error, data) => {
        if (error) {
          console.log(error);
        }
        console.log(data)
      });
    }
  } else if (process.argv[2] == "Visible") {
    if (process.argv[3] == "Activar") {
      console.log(process.argv[4] + " Encender")
      obs.sendCallback('SetSceneItemProperties', {
        'item': process.argv[4],
        'visible': true
      }, (error, data) => {
        if (error) {
          console.log(error);
        }
        console.log(data)
      });
    } else if (process.argv[3] == "Desactivar") {
      console.log(process.argv[4] + " Encender")
      obs.sendCallback('SetSceneItemProperties', {
        'item': process.argv[4],
        'visible': false
      }, (error, data) => {
        if (error) {
          console.log(error);
        }
        console.log(data)
      });
    }
  }

  obs.disconnect();
}).catch(err => {
  console.log(err);
});

obs.on('error', err => {
  console.error('socket error:', err);
});
